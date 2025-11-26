# Makefile for GAX Blockchain C++ Implementation
# Requires: g++, OpenSSL, jsoncpp

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
INCLUDES = -I/usr/include -I/usr/local/include
LIBS = -lssl -lcrypto -ljsoncpp -lpthread
TARGET = gax_blockchain
PYTHON_MODULE = gax_blockchain.so

# Source files
SRCS = blockchain_main.cpp
OBJS = $(SRCS:.cpp=.o)

# Headers
HEADERS = blockchain.h

# Default target
all: $(TARGET)

# Build executable
$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LIBS)
	@echo "✓ GAX Blockchain built successfully!"
	@echo "Run with: ./$(TARGET)"

# Build Python shared library
python: blockchain_python.cpp $(HEADERS)
	$(CXX) $(CXXFLAGS) -shared -fPIC blockchain_python.cpp -o $(PYTHON_MODULE) \
		$(INCLUDES) $(LIBS) \
		-I/usr/include/python3.10 -lpython3.10
	@echo "✓ Python module built: $(PYTHON_MODULE)"

# Compile object files
%.o: %.cpp $(HEADERS)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Clean build files
clean:
	rm -f $(OBJS) $(TARGET) $(PYTHON_MODULE) *.o
	@echo "✓ Cleaned build files"

# Install dependencies (Ubuntu/Debian)
install-deps:
	@echo "Installing dependencies..."
	sudo apt-get update
	sudo apt-get install -y g++ libssl-dev libjsoncpp-dev python3-dev
	@echo "✓ Dependencies installed"

# Run the blockchain demo
run: $(TARGET)
	./$(TARGET)

# Run tests
test: $(TARGET)
	@echo "Running blockchain tests..."
	./$(TARGET)
	@echo "✓ Tests completed"

# Build with debug symbols
debug: CXXFLAGS += -g -DDEBUG
debug: clean $(TARGET)
	@echo "✓ Debug build complete"

# Check for memory leaks
valgrind: debug
	valgrind --leak-check=full --show-leak-kinds=all ./$(TARGET)

.PHONY: all clean install-deps run test debug python valgrind
