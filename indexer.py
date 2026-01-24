import os
import time
import logging
import threading
import database
import config

class Indexer:
    def __init__(self, include_dirs, exclude_dirs=None):
        self.include_dirs = include_dirs
        self.exclude_dirs = exclude_dirs or []
        # Load from DB immediately for fast startup
        self.files, self.directories = database.db.get_index()
        self.last_scan = 0
        self.is_scanning = False

    def _is_excluded(self, path):
        for exclude in self.exclude_dirs:
            if path.startswith(exclude):
                return True
        return False

    def scan_async(self):
        if self.is_scanning:
            return
        threading.Thread(target=self.scan, daemon=True).start()

    def scan(self):
        """Recursively scans the directories and builds a list of files and directories."""
        self.is_scanning = True
        logging.info(f"Scanning...")
        start_time = time.time()
        file_list = []
        dir_list = []
        
        seen_paths = set()

        for root_dir in self.include_dirs:
            if not os.path.exists(root_dir):
                continue
            
            # Add root dir itself if not excluded
            if root_dir not in seen_paths and not self._is_excluded(root_dir):
                dir_list.append(root_dir)
                seen_paths.add(root_dir)

            try:
                for root, dirs, files in os.walk(root_dir, followlinks=True):
                    # Loop Detection: Verify if we've seen this real path before
                    real_root = os.path.realpath(root)
                    if real_root in seen_paths:
                        # We might have entered a loop or just a diamond. 
                        # Ideally os.walk with followlinks handles simple recursion, but let's be safe.
                        # Actually, os.walk(followlinks=True) DOES NOT protect against infinite loops in Python < 3.10 approx? 
                        # In standard python os.walk, it can loop efficiently. 
                        # We must track visited REAL paths of directories we descend into.
                        # But here, 'root' changes as we walk.
                        # If we track all files, we might be fine, but let's be explicitly careful with dirs.
                        pass
                    
                    # Instead of complex walk manipulation, let's just use strict realpath tracking for what we add.
                    
                    # Prune excluded directories and hidden directories
                    # Also prune if we've already processed this real directory to prevent loops
                    i = 0
                    while i < len(dirs):
                        d = dirs[i]
                        full_path = os.path.join(root, d)
                        real_path = os.path.realpath(full_path)
                        
                        if d.startswith('.') or self._is_excluded(full_path) or real_path in seen_paths:
                            del dirs[i]
                        else:
                            # We mark it as seen now, so we don't process it again via another link or loop
                            seen_paths.add(real_path)
                            # Also add to results
                            dir_list.append(full_path) 
                            i += 1
                    
                    for file in files:
                        if not file.startswith('.'):
                            full_path = os.path.join(root, file)
                            # We might accept symlinked files too
                            if full_path not in seen_paths and not self._is_excluded(full_path):
                                file_list.append(full_path)
                                seen_paths.add(full_path) # Treating files by path, not realpath? 
                                # If we want to dedup files by content/inode, we should use realpath.
                                # But for search, maybe we want both aliases?
                                # User said "scan soft links as well - so long as the soft links are not an infinite loop".
                                # Loops only happen with directories. Files are fine.
            except Exception as e:
                logging.error(f"Error scanning {root_dir}: {e}")

        # Update Memory
        self.files = file_list
        self.directories = dir_list
        self.last_scan = time.time()
        
        # Update Database
        database.db.update_index(self.files, self.directories)
        
        # Update Config Last Scan Time
        # We need to load config, update, save. 
        # But we are in indexer... better to just update the specific setting via DB or generic config?
        # Let's simple use config module
        conf = config.load_config()
        conf['last_scan'] = self.last_scan
        config.save_config(conf)
        
        logging.info(f"Scanned {len(self.directories)} directories and {len(self.files)} files in {self.last_scan - start_time:.4f}s")
        self.is_scanning = False
    
    def search(self, query, limit=50):
        """
        Search for files and directories.
        - Directories: specific path component matching query is returned.
                       (e.g. search 'foo' in 'a/b/foo/d' returns 'a/b/foo')
        - Files: ONLY matches if filename matches query.
        """
        if not query:
            return []
        
        query = query.lower()
        results_set = set() # For deduplication
        dir_results = []
        file_results = []
        
        # 1. Search Directories (with path collapsing)
        for path in self.directories:
            # Quick check if query is in path at all to save time
            path_lower = path.lower()
            if query in path_lower:
                # Iterate components to find the *first* match from root
                # actually, usually we want the first match from root to collapse it?
                # User said: "if searching for d, only show a/b/c/d" (deepest match?)
                # "if user searches for b, only show a/b" (shallow match)
                # So we iterate parts, find match, stop there.
                
                parts = path.split(os.sep)
                # Reconstruct path and check components
                # Handle absolute paths starting with /
                current_path = ""
                if path.startswith(os.sep):
                    parts = parts[1:] # Skip empty first element from split
                    current_path = os.sep
                
                for part in parts:
                    if not part: continue
                    current_path = os.path.join(current_path, part)
                    if query in part.lower():
                        if current_path not in results_set:
                            dir_results.append(current_path)
                            results_set.add(current_path)
                        # We break here to only show the top-most match in this specific path chain
                        # If we have a/b/b/d and search b, we get a/b. 
                        # This avoids listing a/b AND a/b/b for the same underlying path.
                        break
            
            if len(results_set) >= limit:
                break
        
        if len(results_set) >= limit:
            return dir_results

        # 2. Search Files (Strict filename match)
        for path in self.files:
            filename = os.path.basename(path)
            if query in filename.lower():
                if path not in results_set:
                    file_results.append(path)
                    results_set.add(path)
                    
            if len(results_set) >= limit:
                break
                    
        return dir_results + file_results
