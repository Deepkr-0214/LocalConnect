// User-specific localStorage utility
const UserStorage = {
    userId: '{{ user_id }}',
    
    getKey(key) {
        return `user_${this.userId}_${key}`;
    },
    
    setItem(key, value) {
        localStorage.setItem(this.getKey(key), value);
    },
    
    getItem(key) {
        return localStorage.getItem(this.getKey(key));
    },
    
    removeItem(key) {
        localStorage.removeItem(this.getKey(key));
    }
};
