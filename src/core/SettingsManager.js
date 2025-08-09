export class SettingsManager {
    get(key, defaultValue) {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : defaultValue;
    }

    set(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }
}
