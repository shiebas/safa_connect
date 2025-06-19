import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'https://safa.org.za'; // Change to your actual server URL
// For development, you might use:
// const BASE_URL = 'http://10.0.2.2:8000'; // Android emulator pointing to localhost
// const BASE_URL = 'http://localhost:8000'; // iOS simulator

/**
 * API Service for managing communication with the SAFA backend
 */
class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to add auth token to requests
    this.api.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Token ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle 401 Unauthorized errors (token expired)
        if (error.response && error.response.status === 401) {
          // Clear token and navigate to login (this will be handled in the components)
          AsyncStorage.removeItem('authToken');
          // We'll emit an event that the app can listen to
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Authenticate user and get token
   * @param {string} username User's email or username
   * @param {string} password User's password
   * @returns Promise with auth token
   */
  async login(username, password) {
    try {
      const response = await this.api.post('/accounts/api/login/', {
        username,
        password,
      });
      if (response.data.token) {
        await AsyncStorage.setItem('authToken', response.data.token);
      }
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Log out the user
   */
  async logout() {
    try {
      // Call logout endpoint if available
      await this.api.post('/accounts/api/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear stored tokens
      await AsyncStorage.removeItem('authToken');
    }
  }

  /**
   * Get current user profile
   * @returns Promise with user profile data
   */
  async getUserProfile() {
    try {
      const response = await this.api.get('/accounts/api/profile/');
      return response.data;
    } catch (error) {
      console.error('Get user profile error:', error);
      throw error;
    }
  }

  /**
   * Get digital card data
   * @returns Promise with digital card data
   */
  async getDigitalCard() {
    try {
      const response = await this.api.get('/membership-cards/api/digitalcards/my-card/');
      return response.data;
    } catch (error) {
      console.error('Get digital card error:', error);
      throw error;
    }
  }

  /**
   * Get QR code data for card
   * @returns Promise with QR code data
   */
  async getCardQR() {
    try {
      const response = await this.api.get('/membership-cards/qr-code/');
      return response.data;
    } catch (error) {
      console.error('Get QR code error:', error);
      throw error;
    }
  }

  /**
   * Verify QR code from scan
   * @param {string} qrData The QR code data to verify
   * @returns Promise with verification result
   */
  async verifyQRCode(qrData) {
    try {
      const response = await this.api.post('/membership-cards/verify/', {
        qr_data: qrData
      });
      return response.data;
    } catch (error) {
      console.error('Verify QR code error:', error);
      throw error;
    }
  }
}

export default new ApiService();
