// Banking API Integration
class BankingAPI {
    constructor(baseUrl = 'https://gax-2.onrender.com') {
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('django_api_token');
    }

    // Helper method for making authenticated requests
    async fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(this.token && { 'Authorization': `Token ${this.token}` }),
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Account Information
    async getAccountInfo() {
        return await this.fetch('/api/accounts/info/');
    }

    // Balance
    async getBalance() {
        return await this.fetch('/api/accounts/balance/');
    }

    // Transactions
    async getTransactions() {
        return await this.fetch('/api/transactions/');
    }

    async createTransaction(data) {
        return await this.fetch('/api/transactions/create/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Money Transfer
    async transfer(data) {
        return await this.fetch('/api/transfer/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Bill Payments
    async payBill(data) {
        return await this.fetch('/api/bills/pay/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getBills() {
        return await this.fetch('/api/bills/');
    }

    // Account Settings
    async updateAccountSettings(data) {
        return await this.fetch('/api/accounts/settings/', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Notifications
    async getNotifications() {
        return await this.fetch('/api/notifications/');
    }

    // Error Handler
    handleError(error) {
        console.error('Banking API Error:', error);
        return {
            success: false,
            error: error.message || 'An error occurred while processing your request'
        };
    }
}
