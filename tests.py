import unittest
import os
import shutil
import tempfile
from pathlib import Path
from indexer import Indexer
import config

class TestFstaSearch(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create some dummy files
        os.makedirs(os.path.join(self.test_dir, "subdir"))
        Path(os.path.join(self.test_dir, "file1.txt")).touch()
        Path(os.path.join(self.test_dir, "file2.py")).touch()
        Path(os.path.join(self.test_dir, "subdir", "file3.jpg")).touch()
        
        # Hidden file
        Path(os.path.join(self.test_dir, ".hidden")).touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_indexer_scan(self):
        indexer = Indexer([self.test_dir])
        indexer.scan()
        
        # Should find 3 files and 2 directories (test_dir, subdir)
        self.assertEqual(len(indexer.files), 3)
        self.assertEqual(len(indexer.directories), 2)
        self.assertTrue(any("file1.txt" in f for f in indexer.files))
        self.assertTrue(any("subdir" in d for d in indexer.directories))

    def test_indexer_exclude(self):
        # Exclude the subdir
        subdir = os.path.join(self.test_dir, "subdir")
        indexer = Indexer([self.test_dir], exclude_dirs=[subdir])
        indexer.scan()
        
        # Should find only 2 files (file1, file2)
        # Should find 1 directory (test_dir)
        self.assertEqual(len(indexer.files), 2)
        self.assertEqual(len(indexer.directories), 1)
        self.assertFalse(any("file3.jpg" in f for f in indexer.files))

    def test_indexer_search(self):
        indexer = Indexer([self.test_dir])
        indexer.scan()
        
        results = indexer.search("file1")
        self.assertEqual(len(results), 1)
        self.assertTrue("file1.txt" in results[0])

    def test_search_prioritization_and_collapsing(self):
        """Test directory collapsing and prioritization."""
        # Structure:
        # test_dir/
        #   subdir/
        #     deepfile.txt
        #   subdir_file.txt
        
        Path(os.path.join(self.test_dir, "subdir_file.txt")).touch()
        subdir = os.path.join(self.test_dir, "subdir")
        deepfile = os.path.join(subdir, "deepfile.txt")
        Path(deepfile).touch()
        
        indexer = Indexer([self.test_dir])
        indexer.scan()
        
        # 1. Search for 'sub' - should match 'subdir' folder
        results = indexer.search("sub")
        # Should contain path/to/subdir
        # Should NOT contain paths like path/to/subdir/file if they don't match strict filename rule
        # 'deepfile.txt' does not contain 'sub', so it shouldn't show up.
        # 'subdir_file.txt' contains 'sub', so it SHOULD show up.
        
        self.assertTrue(any(r.endswith("subdir") for r in results))
        self.assertTrue(any(r.endswith("subdir_file.txt") for r in results))
        self.assertFalse(any("deepfile.txt" in r for r in results))
        
        # 2. Collapsing Test
        # Create a/b/c structure
        os.makedirs(os.path.join(self.test_dir, "a", "b", "c"), exist_ok=True)
        indexer.scan()
        
        # Search for 'a' -> should return .../a
        # Should NOT return .../a/b or .../a/b/c
        results_a = indexer.search("a")
        
        # Filter for the 'a' directory path
        a_matches = [r for r in results_a if r.endswith(os.sep + "a")]
        self.assertEqual(len(a_matches), 1)
        
        # Ensure deep paths are not included as separate entries just because 'a' is in the root
        # .../a/b shouldn't be in results unless 'b' has 'a' in it (it doesn't).
        self.assertFalse(any(r.endswith(os.path.join("a", "b")) for r in results_a))

        # Search for 'b' -> should return .../a/b
        results_b = indexer.search("b")
        self.assertTrue(any(r.endswith(os.path.join("a", "b")) for r in results_b))
        
        # Search for 'c' -> should return .../a/b/c
        results_c = indexer.search("c")
        self.assertTrue(any(r.endswith(os.path.join("a", "b", "c")) for r in results_c))

    def test_config_defaults(self):
        # Test default config logic
        defaults = config.DEFAULT_CONFIG
        self.assertTrue("include_directories" in defaults)

if __name__ == '__main__':
    unittest.main()
