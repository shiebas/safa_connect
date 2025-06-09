import axios from 'axios';
import { StorageService } from './StorageService';

const API_BASE_URL = 'https://your-safa-domain.com'; // Update with your domain

class CardServiceClass {
  async getApiHeaders() {
    const token = await StorageService.getToken();
    return {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    };
  }

  async getMyCard() {
    try {
      const headers = await this.getApiHeaders();
      const response = await axios.get(`${API_BASE_URL}/cards/my-card/`, { headers });
      return response.data;
    } catch (error) {
      console.log('Get card error:', error);
      throw error;
    }
  }

  async verifyQRCode(qrData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/cards/verify/`, {
        qr_data: qrData
      });
      return response.data;
    } catch (error) {
      console.log('Verify QR error:', error);
      throw error;
    }
  }

  async getQRCodeData() {
    try {
      const headers = await this.getApiHeaders();
      const response = await axios.get(`${API_BASE_URL}/cards/qr-code/`, { headers });
      return response.data;
    } catch (error) {
      console.log('Get QR data error:', error);
      throw error;
    }
  }
}

export const CardService = new CardServiceClass();
