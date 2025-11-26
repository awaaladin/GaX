#include <iostream>
#include <string>
#include <vector>
#include <ctime>
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>
#include <chrono>

std::string sha256(const std::string& data) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, data.c_str(), data.size());
    SHA256_Final(hash, &sha256);
    
    std::stringstream ss;
    for(int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return ss.str();
}

class Block {
public:
    int index;
    long long timestamp;
    std::string data;
    std::string previousHash;
    std::string hash;
    int nonce;
    
    Block(int idx, const std::string& blockData, const std::string& prevHash)
        : index(idx), data(blockData), previousHash(prevHash), nonce(0) {
        timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count();
        hash = calculateHash();
    }
    
    std::string calculateHash() const {
        std::stringstream ss;
        ss << index << timestamp << data << previousHash << nonce;
        return sha256(ss.str());
    }
    
    void mineBlock(int difficulty) {
        std::string target(difficulty, '0');
        std::cout << "Mining block " << index << "...\n";
        auto start = std::chrono::high_resolution_clock::now();
        
        while (hash.substr(0, difficulty) != target) {
            nonce++;
            hash = calculateHash();
        }
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        
        std::cout << "Block mined: " << hash << "\n";
        std::cout << "Nonce: " << nonce << " | Time: " << duration.count() << "ms\n";
    }
};

class Blockchain {
private:
    std::vector<Block> chain;
    int difficulty;
    
public:
    Blockchain(int diff = 4) : difficulty(diff) {
        chain.emplace_back(0, "Genesis Block", "0");
        std::cout << "Genesis block created\n";
    }
    
    Block getLatestBlock() const {
        return chain.back();
    }
    
    void addBlock(Block newBlock) {
        newBlock.previousHash = getLatestBlock().hash;
        newBlock.mineBlock(difficulty);
        chain.push_back(newBlock);
    }
    
    bool isChainValid() const {
        for (size_t i = 1; i < chain.size(); i++) {
            const Block& currentBlock = chain[i];
            const Block& previousBlock = chain[i - 1];
            
            if (currentBlock.hash != currentBlock.calculateHash()) {
                std::cout << "❌ Invalid hash at block " << i << "\n";
                return false;
            }
            
            if (currentBlock.previousHash != previousBlock.hash) {
                std::cout << "❌ Invalid previous hash at block " << i << "\n";
                return false;
            }
            
            std::string target(difficulty, '0');
            if (currentBlock.hash.substr(0, difficulty) != target) {
                std::cout << "❌ Invalid proof of work at block " << i << "\n";
                return false;
            }
        }
        return true;
    }
    
    void printChain() const {
        std::cout << "\n╔════════════════════════════════════════════════╗\n";
        std::cout << "║           BLOCKCHAIN STATE                     ║\n";
        std::cout << "╚════════════════════════════════════════════════╝\n";
        
        for (const auto& block : chain) {
            std::cout << "\n┌─ Block " << block.index << " " << std::string(40, '─') << "\n";
            std::cout << "│ Timestamp: " << block.timestamp << "\n";
            std::cout << "│ Data: " << block.data << "\n";
            std::cout << "│ Previous: " << block.previousHash.substr(0, 16) << "...\n";
            std::cout << "│ Hash:     " << block.hash.substr(0, 16) << "...\n";
            std::cout << "│ Nonce: " << block.nonce << "\n";
            std::cout << "└" << std::string(50, '─') << "\n";
        }
    }
    
    Block& getBlock(int index) {
        return chain[index];
    }
    
    size_t getChainSize() const {
        return chain.size();
    }
};

int main() {
    std::cout << "\n🔗 Bitcoin-Style Blockchain Implementation\n";
    std::cout << "=========================================\n\n";
    
    Blockchain blockchain(4);
    
    std::cout << "\n📦 Adding Block 1...\n";
    blockchain.addBlock(Block(1, "Transaction: Alice -> Bob 50 BTC", ""));
    
    std::cout << "\n📦 Adding Block 2...\n";
    blockchain.addBlock(Block(2, "Transaction: Bob -> Charlie 25 BTC", ""));
    
    std::cout << "\n📦 Adding Block 3...\n";
    blockchain.addBlock(Block(3, "Transaction: Charlie -> Dave 10 BTC", ""));
    
    blockchain.printChain();
    
    std::cout << "\n✅ Validating blockchain...\n";
    bool valid = blockchain.isChainValid();
    std::cout << (valid ? "✅ Blockchain is VALID\n" : "❌ Blockchain is INVALID\n");
    
    std::cout << "\n🔧 Tampering with Block 2...\n";
    blockchain.getBlock(2).data = "Transaction: Bob -> Charlie 1000 BTC (TAMPERED)";
    
    std::cout << "\n✅ Re-validating blockchain...\n";
    valid = blockchain.isChainValid();
    std::cout << (valid ? "✅ Blockchain is VALID\n" : "❌ Blockchain is INVALID (tampering detected)\n");
    
    return 0;
}
