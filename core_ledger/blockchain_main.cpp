/*
 * GAX Blockchain - Main Entry Point
 * 
 * This file demonstrates usage of the blockchain and provides
 * a command-line interface for blockchain operations
 */

#include "blockchain.h"
#include <iostream>
#include <fstream>
#include <json/json.h>  // You'll need jsoncpp library

using namespace gax;
using namespace std;

/**
 * Wallet class - Manages public/private key pairs
 * In production, this would use proper ECDSA key generation
 */
class Wallet {
private:
    string privateKey;
    string publicKey;
    string address;
    
public:
    Wallet() {
        // In production: Generate EC key pair using OpenSSL
        // For now, simplified version
        generateKeys();
    }
    
    void generateKeys() {
        // Simplified: In production use ECDSA secp256k1
        privateKey = Utils::sha256(to_string(Utils::getCurrentTimestamp()));
        publicKey = Utils::sha256(privateKey);
        address = Utils::sha256(publicKey).substr(0, 40);  // First 40 chars
    }
    
    string getAddress() const {
        return address;
    }
    
    string getPublicKey() const {
        return publicKey;
    }
    
    /**
     * Sign transaction (simplified)
     * In production: Use ECDSA signature
     */
    string sign(const string& data) const {
        return Utils::sha256(data + privateKey);
    }
    
    /**
     * Create transaction from this wallet
     */
    Transaction createTransaction(const string& recipientAddress, double amount, 
                                  Blockchain& blockchain) {
        Transaction tx(address, "transfer");
        
        // Get UTXOs for this address
        vector<TransactionOutput> myUTXOs = blockchain.getUTXOPool().getUTXOsForAddress(address);
        
        double total = 0.0;
        for(const auto& utxo : myUTXOs) {
            if(total >= amount) break;
            
            TransactionInput input(utxo.txHash, utxo.index);
            input.publicKey = publicKey;
            input.signature = sign(utxo.txHash + to_string(utxo.index));
            
            tx.addInput(input);
            total += utxo.amount;
        }
        
        if(total < amount) {
            throw runtime_error("Insufficient balance");
        }
        
        // Output to recipient
        TransactionOutput output(recipientAddress, amount);
        tx.addOutput(output);
        
        // Change back to sender
        if(total > amount) {
            TransactionOutput change(address, total - amount);
            tx.addOutput(change);
        }
        
        tx.finalize();
        return tx;
    }
};

/**
 * Blockchain Node - Manages blockchain and provides API
 */
class BlockchainNode {
private:
    Blockchain blockchain;
    vector<Transaction> pendingTransactions;
    Wallet minerWallet;
    
public:
    BlockchainNode(int difficulty = 4) : blockchain(difficulty) {
        cout << "GAX Blockchain Node initialized" << endl;
        cout << "Miner address: " << minerWallet.getAddress() << endl;
    }
    
    void addTransaction(const Transaction& tx) {
        if(tx.verify()) {
            pendingTransactions.push_back(tx);
            cout << "Transaction added to pool" << endl;
        } else {
            cout << "Invalid transaction rejected" << endl;
        }
    }
    
    void minePendingTransactions() {
        cout << "\n=== Mining new block ===" << endl;
        cout << "Pending transactions: " << pendingTransactions.size() << endl;
        
        blockchain.mineBlock(minerWallet.getAddress(), pendingTransactions);
        pendingTransactions.clear();
        
        cout << "Block mined successfully!" << endl;
        cout << "Miner balance: " << blockchain.getBalance(minerWallet.getAddress()) << " GAX" << endl;
    }
    
    void printBlockchain() const {
        cout << "\n=== GAX Blockchain ===" << endl;
        cout << "Chain length: " << blockchain.getChainLength() << endl;
        cout << "Difficulty: " << blockchain.getDifficulty() << endl;
        cout << "Is valid: " << (blockchain.verify() ? "Yes" : "No") << endl;
        
        for(const auto& block : blockchain.getChain()) {
            cout << "\n--- Block " << block.getIndex() << " ---" << endl;
            cout << "Hash: " << block.getHash() << endl;
            cout << "Previous: " << block.getPreviousHash() << endl;
            cout << "Merkle Root: " << block.getMerkleRoot() << endl;
            cout << "Nonce: " << block.getNonce() << endl;
            cout << "Timestamp: " << block.getTimestamp() << endl;
            cout << "Transactions: " << block.getTransactions().size() << endl;
            
            for(const auto& tx : block.getTransactions()) {
                cout << "  - TX: " << tx.getHash().substr(0, 16) << "..." << endl;
                cout << "    Type: " << tx.getType() << endl;
                cout << "    Outputs: " << tx.getOutputs().size() << endl;
            }
        }
    }
    
    double getBalance(const string& address) const {
        return blockchain.getBalance(address);
    }
    
    Blockchain& getBlockchain() {
        return blockchain;
    }
    
    Wallet& getMinerWallet() {
        return minerWallet;
    }
};

/**
 * REST API Interface (to be called from Python/FastAPI)
 */
extern "C" {
    // Global node instance
    static BlockchainNode* node = nullptr;
    
    /**
     * Initialize blockchain
     */
    void init_blockchain(int difficulty) {
        if(node == nullptr) {
            node = new BlockchainNode(difficulty);
        }
    }
    
    /**
     * Get balance for address
     */
    double get_balance(const char* address) {
        if(node == nullptr) return 0.0;
        return node->getBalance(string(address));
    }
    
    /**
     * Mine new block
     */
    void mine_block() {
        if(node != nullptr) {
            node->minePendingTransactions();
        }
    }
    
    /**
     * Get chain length
     */
    int get_chain_length() {
        if(node == nullptr) return 0;
        return node->getBlockchain().getChainLength();
    }
    
    /**
     * Verify blockchain
     */
    bool verify_chain() {
        if(node == nullptr) return false;
        return node->getBlockchain().verify();
    }
}

/**
 * Main function - Demonstration
 */
int main() {
    cout << "============================================" << endl;
    cout << "  GAX Blockchain - Bitcoin-like System" << endl;
    cout << "============================================\n" << endl;
    
    // Create blockchain node
    BlockchainNode node(4);  // Difficulty 4
    
    // Create wallets
    Wallet alice, bob;
    cout << "\nWallets created:" << endl;
    cout << "Alice: " << alice.getAddress() << endl;
    cout << "Bob: " << bob.getAddress() << endl;
    
    // Mine first block (empty, just mining reward)
    cout << "\n--- Mining Genesis Reward ---" << endl;
    node.minePendingTransactions();
    
    // Create transaction from miner to Alice
    try {
        cout << "\n--- Transaction: Miner -> Alice (25 GAX) ---" << endl;
        Transaction tx1 = node.getMinerWallet().createTransaction(
            alice.getAddress(), 25.0, node.getBlockchain()
        );
        node.addTransaction(tx1);
        node.minePendingTransactions();
        
        cout << "Alice balance: " << node.getBalance(alice.getAddress()) << " GAX" << endl;
    } catch(const exception& e) {
        cout << "Error: " << e.what() << endl;
    }
    
    // Transaction from Alice to Bob
    try {
        cout << "\n--- Transaction: Alice -> Bob (10 GAX) ---" << endl;
        Transaction tx2 = alice.createTransaction(
            bob.getAddress(), 10.0, node.getBlockchain()
        );
        node.addTransaction(tx2);
        node.minePendingTransactions();
        
        cout << "Alice balance: " << node.getBalance(alice.getAddress()) << " GAX" << endl;
        cout << "Bob balance: " << node.getBalance(bob.getAddress()) << " GAX" << endl;
    } catch(const exception& e) {
        cout << "Error: " << e.what() << endl;
    }
    
    // Print blockchain
    node.printBlockchain();
    
    // Verify blockchain
    cout << "\n=== Blockchain Verification ===" << endl;
    if(node.getBlockchain().verify()) {
        cout << "✓ Blockchain is valid!" << endl;
    } else {
        cout << "✗ Blockchain is corrupted!" << endl;
    }
    
    return 0;
}
