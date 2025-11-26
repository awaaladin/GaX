"""
Python bindings for GAX C++ Blockchain
Allows Python/Django to interact with the C++ blockchain implementation
"""

import ctypes
import os
from pathlib import Path

class BlockchainBinding:
    """
    Python wrapper for C++ blockchain library
    """
    
    def __init__(self, lib_path=None):
        if lib_path is None:
            # Try to find the .so file
            current_dir = Path(__file__).parent
            lib_path = current_dir / "gax_blockchain.so"
        
        if not os.path.exists(lib_path):
            raise FileNotFoundError(
                f"Blockchain library not found at {lib_path}. "
                f"Run 'make python' to build it."
            )
        
        # Load shared library
        self.lib = ctypes.CDLL(str(lib_path))
        
        # Define function signatures
        self.lib.init_blockchain.argtypes = [ctypes.c_int]
        self.lib.init_blockchain.restype = None
        
        self.lib.get_balance.argtypes = [ctypes.c_char_p]
        self.lib.get_balance.restype = ctypes.c_double
        
        self.lib.mine_block.argtypes = []
        self.lib.mine_block.restype = None
        
        self.lib.get_chain_length.argtypes = []
        self.lib.get_chain_length.restype = ctypes.c_int
        
        self.lib.verify_chain.argtypes = []
        self.lib.verify_chain.restype = ctypes.c_bool
        
        # Initialize blockchain
        self.lib.init_blockchain(4)  # Difficulty 4
    
    def get_balance(self, address: str) -> float:
        """Get balance for a blockchain address"""
        return self.lib.get_balance(address.encode('utf-8'))
    
    def mine_block(self):
        """Mine a new block with pending transactions"""
        self.lib.mine_block()
    
    def get_chain_length(self) -> int:
        """Get current blockchain length"""
        return self.lib.get_chain_length()
    
    def verify_chain(self) -> bool:
        """Verify blockchain integrity"""
        return self.lib.verify_chain()


# Singleton instance
_blockchain = None

def get_blockchain():
    """Get global blockchain instance"""
    global _blockchain
    if _blockchain is None:
        _blockchain = BlockchainBinding()
    return _blockchain
