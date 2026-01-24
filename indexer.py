import os
import time

class Indexer:
    def __init__(self, include_dirs, exclude_dirs=None):
        self.include_dirs = include_dirs
        self.exclude_dirs = exclude_dirs or []
        self.files = []
        self.directories = []
        self.last_scan = 0

    def _is_excluded(self, path):
        for exclude in self.exclude_dirs:
            if path.startswith(exclude):
                return True
        return False

    def scan(self):
        """Recursively scans the directories and builds a list of files and directories."""
        print(f"Scanning...")
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
                for root, dirs, files in os.walk(root_dir):
                    # Prune excluded directories and hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and not self._is_excluded(os.path.join(root, d))]
                    
                    for d in dirs:
                         full_path = os.path.join(root, d)
                         if full_path not in seen_paths:
                             dir_list.append(full_path)
                             seen_paths.add(full_path)

                    for file in files:
                        if not file.startswith('.'):
                            full_path = os.path.join(root, file)
                            if full_path not in seen_paths and not self._is_excluded(full_path):
                                file_list.append(full_path)
                                seen_paths.add(full_path)
            except Exception as e:
                print(f"Error scanning {root_dir}: {e}")

        self.files = file_list
        self.directories = dir_list
        self.last_scan = time.time()
        print(f"Scanned {len(self.directories)} directories and {len(self.files)} files in {self.last_scan - start_time:.4f}s")
    
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
