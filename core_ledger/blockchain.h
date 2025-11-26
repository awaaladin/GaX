/*
 * GAX Blockchain - Bitcoin-like Blockchain Implementation in C++
 * 
 * Features:
 * - Proof of Work (PoW) consensus
 * - SHA-256 hashing
 * - UTXO (Unspent Transaction Output) model
 * - Wallet management with public/private keys
 * - Transaction verification
 * - Block mining with difficulty adjustment
 * - Merkle tree for transaction verification
 * 
 * Author: GAX Development Team
 * License: MIT
 */

#ifndef BLOCKCHAIN_H
#define BLOCKCHAIN_H

#include <string>
#include <vector>
#include <ctime>
#include <sstream>
#include <iomanip>
#include <memory>
#include <map>
#include <openssl/sha.h>
#include <openssl/ec.h>
#include <openssl/ecdsa.h>
#include <openssl/obj_mac.h>

namespace gax {

// Forward declarations
class Transaction;
class Block;
class Blockchain;
class Wallet;

/**
 * Utility functions for blockchain operations
 */
class Utils {
public:
    /**
     * Calculate SHA-256 hash of input string
     */
    static std::string sha256(const std::string& input) {
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256_CTX sha256;
        SHA256_Init(&sha256);
        SHA256_Update(&sha256, input.c_str(), input.size());
        SHA256_Final(hash, &sha256);
        
        std::stringstream ss;
        for(int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
            ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(hash[i]);
        }
        return ss.str();
    }
    
    /**
     * Get current Unix timestamp
     */
    static long long getCurrentTimestamp() {
        return static_cast<long long>(std::time(nullptr));
    }
    
    /**
     * Convert double to string with precision
     */
    static std::string doubleToString(double value, int precision = 8) {
        std::ostringstream out;
        out << std::fixed << std::setprecision(precision) << value;
        return out.str();
    }
};

/**
 * Transaction Input - References previous transaction output
 */
struct TransactionInput {
    std::string previousTxHash;  // Hash of previous transaction
    int outputIndex;              // Index of output in previous transaction
    std::string signature;        // Digital signature
    std::string publicKey;        // Public key of spender
    
    TransactionInput(const std::string& prevHash, int outIdx)
        : previousTxHash(prevHash), outputIndex(outIdx) {}
};

/**
 * Transaction Output - Specifies amount and recipient
 */
struct TransactionOutput {
    std::string recipientAddress;  // Address of recipient (hash of public key)
    double amount;                 // Amount in GAX tokens
    std::string txHash;            // Hash of transaction containing this output
    int index;                     // Index in transaction outputs
    
    TransactionOutput(const std::string& addr, double amt)
        : recipientAddress(addr), amount(amt), index(0) {}
    
    bool isSpendableBy(const std::string& address) const {
        return recipientAddress == address;
    }
};

/**
 * Transaction class - Represents transfer of GAX tokens
 */
class Transaction {
private:
    std::string txHash;
    std::vector<TransactionInput> inputs;
    std::vector<TransactionOutput> outputs;
    long long timestamp;
    std::string senderAddress;
    std::string type;  // "transfer", "coinbase", "premium", "purchase"
    std::string metadata;  // JSON metadata for additional info
    
public:
    Transaction(const std::string& sender, const std::string& txType = "transfer")
        : senderAddress(sender), type(txType), timestamp(Utils::getCurrentTimestamp()) {}
    
    void addInput(const TransactionInput& input) {
        inputs.push_back(input);
    }
    
    void addOutput(const TransactionOutput& output) {
        outputs.push_back(output);
    }
    
    void setMetadata(const std::string& meta) {
        metadata = meta;
    }
    
    /**
     * Calculate transaction hash
     */
    std::string calculateHash() const {
        std::stringstream ss;
        ss << senderAddress << timestamp << type;
        
        for(const auto& input : inputs) {
            ss << input.previousTxHash << input.outputIndex;
        }
        
        for(const auto& output : outputs) {
            ss << output.recipientAddress << Utils::doubleToString(output.amount);
        }
        
        ss << metadata;
        return Utils::sha256(ss.str());
    }
    
    void finalize() {
        txHash = calculateHash();
        // Set transaction hash for all outputs
        for(size_t i = 0; i < outputs.size(); i++) {
            outputs[i].txHash = txHash;
            outputs[i].index = i;
        }
    }
    
    /**
     * Verify transaction is valid
     */
    bool verify() const {
        // Basic validation
        if(inputs.empty() && type != "coinbase") {
            return false;  // Non-coinbase tx must have inputs
        }
        
        if(outputs.empty()) {
            return false;  // Must have at least one output
        }
        
        // Calculate total input and output amounts
        double totalInput = 0.0;
        double totalOutput = 0.0;
        
        for(const auto& output : outputs) {
            if(output.amount <= 0) return false;
            totalOutput += output.amount;
        }
        
        // For coinbase transactions (mining rewards)
        if(type == "coinbase") {
            return totalOutput <= 50.0;  // Max coinbase reward
        }
        
        // TODO: Verify signatures on inputs
        // TODO: Verify inputs reference valid UTXOs
        
        return true;
    }
    
    // Getters
    std::string getHash() const { return txHash; }
    std::string getSender() const { return senderAddress; }
    std::string getType() const { return type; }
    const std::vector<TransactionInput>& getInputs() const { return inputs; }
    const std::vector<TransactionOutput>& getOutputs() const { return outputs; }
    long long getTimestamp() const { return timestamp; }
    std::string getMetadata() const { return metadata; }
};

/**
 * Merkle Tree - For efficient transaction verification
 */
class MerkleTree {
private:
    std::vector<std::string> leaves;
    std::string root;
    
    std::string combinedHash(const std::string& left, const std::string& right) {
        return Utils::sha256(left + right);
    }
    
public:
    void addLeaf(const std::string& hash) {
        leaves.push_back(hash);
    }
    
    std::string calculateRoot() {
        if(leaves.empty()) return "";
        if(leaves.size() == 1) return leaves[0];
        
        std::vector<std::string> currentLevel = leaves;
        
        while(currentLevel.size() > 1) {
            std::vector<std::string> nextLevel;
            
            for(size_t i = 0; i < currentLevel.size(); i += 2) {
                if(i + 1 < currentLevel.size()) {
                    nextLevel.push_back(combinedHash(currentLevel[i], currentLevel[i + 1]));
                } else {
                    // Odd number - duplicate last hash
                    nextLevel.push_back(combinedHash(currentLevel[i], currentLevel[i]));
                }
            }
            
            currentLevel = nextLevel;
        }
        
        root = currentLevel[0];
        return root;
    }
    
    std::string getRoot() const { return root; }
};

/**
 * Block class - Container for transactions with PoW
 */
class Block {
private:
    int index;
    long long timestamp;
    std::vector<Transaction> transactions;
    std::string previousHash;
    std::string hash;
    std::string merkleRoot;
    int nonce;
    int difficulty;
    
public:
    Block(int idx, const std::string& prevHash, int diff = 4)
        : index(idx), previousHash(prevHash), nonce(0), difficulty(diff) {
        timestamp = Utils::getCurrentTimestamp();
    }
    
    void addTransaction(const Transaction& tx) {
        transactions.push_back(tx);
    }
    
    /**
     * Calculate Merkle root of all transactions
     */
    std::string calculateMerkleRoot() {
        MerkleTree tree;
        for(const auto& tx : transactions) {
            tree.addLeaf(tx.getHash());
        }
        return tree.calculateRoot();
    }
    
    /**
     * Calculate block hash (without PoW)
     */
    std::string calculateHash() const {
        std::stringstream ss;
        ss << index << timestamp << previousHash << merkleRoot << nonce << difficulty;
        
        return Utils::sha256(ss.str());
    }
    
    /**
     * Mine block using Proof of Work
     * Find nonce such that hash starts with 'difficulty' number of zeros
     */
    void mineBlock() {
        merkleRoot = calculateMerkleRoot();
        std::string target(difficulty, '0');
        
        std::cout << "Mining block " << index << "..." << std::endl;
        
        do {
            nonce++;
            hash = calculateHash();
        } while(hash.substr(0, difficulty) != target);
        
        std::cout << "Block mined! Hash: " << hash << std::endl;
        std::cout << "Nonce: " << nonce << std::endl;
    }
    
    /**
     * Verify block integrity
     */
    bool verify() const {
        // Verify hash starts with required zeros
        std::string target(difficulty, '0');
        if(hash.substr(0, difficulty) != target) {
            return false;
        }
        
        // Verify hash is correct
        if(hash != calculateHash()) {
            return false;
        }
        
        // Verify all transactions
        for(const auto& tx : transactions) {
            if(!tx.verify()) {
                return false;
            }
        }
        
        return true;
    }
    
    // Getters
    int getIndex() const { return index; }
    std::string getHash() const { return hash; }
    std::string getPreviousHash() const { return previousHash; }
    std::string getMerkleRoot() const { return merkleRoot; }
    int getNonce() const { return nonce; }
    long long getTimestamp() const { return timestamp; }
    const std::vector<Transaction>& getTransactions() const { return transactions; }
    int getDifficulty() const { return difficulty; }
};

/**
 * UTXO Pool - Tracks unspent transaction outputs
 */
class UTXOPool {
private:
    // Map: txHash + outputIndex -> TransactionOutput
    std::map<std::string, TransactionOutput> utxos;
    
    std::string makeKey(const std::string& txHash, int index) const {
        return txHash + ":" + std::to_string(index);
    }
    
public:
    void addUTXO(const TransactionOutput& output) {
        std::string key = makeKey(output.txHash, output.index);
        utxos[key] = output;
    }
    
    void removeUTXO(const std::string& txHash, int index) {
        std::string key = makeKey(txHash, index);
        utxos.erase(key);
    }
    
    TransactionOutput* getUTXO(const std::string& txHash, int index) {
        std::string key = makeKey(txHash, index);
        auto it = utxos.find(key);
        if(it != utxos.end()) {
            return &(it->second);
        }
        return nullptr;
    }
    
    double getBalance(const std::string& address) const {
        double balance = 0.0;
        for(const auto& pair : utxos) {
            if(pair.second.recipientAddress == address) {
                balance += pair.second.amount;
            }
        }
        return balance;
    }
    
    std::vector<TransactionOutput> getUTXOsForAddress(const std::string& address) const {
        std::vector<TransactionOutput> result;
        for(const auto& pair : utxos) {
            if(pair.second.recipientAddress == address) {
                result.push_back(pair.second);
            }
        }
        return result;
    }
};

/**
 * Blockchain class - Main blockchain structure
 */
class Blockchain {
private:
    std::vector<Block> chain;
    int difficulty;
    UTXOPool utxoPool;
    double miningReward;
    
    /**
     * Create genesis block (first block in chain)
     */
    Block createGenesisBlock() {
        Block genesis(0, "0", difficulty);
        
        // Coinbase transaction for genesis
        Transaction coinbase("genesis", "coinbase");
        TransactionOutput genesisOutput("genesis_address", miningReward);
        coinbase.addOutput(genesisOutput);
        coinbase.finalize();
        
        genesis.addTransaction(coinbase);
        genesis.mineBlock();
        
        return genesis;
    }
    
public:
    Blockchain(int diff = 4, double reward = 50.0)
        : difficulty(diff), miningReward(reward) {
        chain.push_back(createGenesisBlock());
    }
    
    /**
     * Add new block to chain
     */
    void addBlock(Block& block) {
        block.mineBlock();
        
        if(block.verify()) {
            chain.push_back(block);
            
            // Update UTXO pool
            for(const auto& tx : block.getTransactions()) {
                // Remove spent UTXOs
                for(const auto& input : tx.getInputs()) {
                    utxoPool.removeUTXO(input.previousTxHash, input.outputIndex);
                }
                
                // Add new UTXOs
                for(const auto& output : tx.getOutputs()) {
                    utxoPool.addUTXO(output);
                }
            }
        }
    }
    
    /**
     * Get latest block
     */
    const Block& getLatestBlock() const {
        return chain.back();
    }
    
    /**
     * Verify entire blockchain integrity
     */
    bool verify() const {
        for(size_t i = 1; i < chain.size(); i++) {
            const Block& currentBlock = chain[i];
            const Block& previousBlock = chain[i - 1];
            
            // Verify block is valid
            if(!currentBlock.verify()) {
                return false;
            }
            
            // Verify chain linkage
            if(currentBlock.getPreviousHash() != previousBlock.getHash()) {
                return false;
            }
        }
        return true;
    }
    
    /**
     * Get balance for address
     */
    double getBalance(const std::string& address) const {
        return utxoPool.getBalance(address);
    }
    
    /**
     * Create and mine new block with pending transactions
     */
    void mineBlock(const std::string& minerAddress, const std::vector<Transaction>& transactions) {
        Block newBlock(chain.size(), getLatestBlock().getHash(), difficulty);
        
        // Add coinbase transaction (mining reward)
        Transaction coinbase(minerAddress, "coinbase");
        TransactionOutput reward(minerAddress, miningReward);
        coinbase.addOutput(reward);
        coinbase.finalize();
        newBlock.addTransaction(coinbase);
        
        // Add other transactions
        for(const auto& tx : transactions) {
            if(tx.verify()) {
                newBlock.addTransaction(tx);
            }
        }
        
        addBlock(newBlock);
    }
    
    // Getters
    const std::vector<Block>& getChain() const { return chain; }
    int getChainLength() const { return chain.size(); }
    int getDifficulty() const { return difficulty; }
    const UTXOPool& getUTXOPool() const { return utxoPool; }
};

} // namespace gax

#endif // BLOCKCHAIN_H
