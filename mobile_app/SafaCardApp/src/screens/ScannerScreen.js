import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  TouchableOpacity,
  Modal,
  ScrollView
} from 'react-native';
import QRCodeScanner from 'react-native-qrcode-scanner';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { CardService } from '../services/CardService';

export default function ScannerScreen() {
  const [scanning, setScanning] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  const onSuccess = async (e) => {
    setScanning(false);
    
    try {
      const result = await CardService.verifyQRCode(e.data);
      setVerificationResult(result);
      setShowResult(true);
    } catch (error) {
      Alert.alert('Verification Failed', 'Unable to verify QR code');
    }
  };

  const startScanning = () => {
    setScanning(true);
  };

  const closeResult = () => {
    setShowResult(false);
    setVerificationResult(null);
  };

  if (scanning) {
    return (
      <View style={styles.scannerContainer}>
        <QRCodeScanner
          onRead={onSuccess}
          flashMode={QRCodeScanner.Constants.FlashMode.auto}
          topContent={
            <Text style={styles.centerText}>
              <Text style={styles.textBold}>Scan SAFA Member QR Code</Text>
            </Text>
          }
          bottomContent={
            <TouchableOpacity 
              style={styles.buttonTouchable} 
              onPress={() => setScanning(false)}
            >
              <Text style={styles.buttonText}>Cancel</Text>
            </TouchableOpacity>
          }
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Icon name="qr-code-scanner" size={100} color="#FFD700" />
        <Text style={styles.title}>QR Code Scanner</Text>
        <Text style={styles.subtitle}>
          Scan SAFA membership cards to verify member status
        </Text>
        
        <TouchableOpacity style={styles.scanButton} onPress={startScanning}>
          <Icon name="camera-alt" size={24} color="#000" />
          <Text style={styles.scanButtonText}>Start Scanning</Text>
        </TouchableOpacity>
      </View>

      {/* Verification Result Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={showResult}
        onRequestClose={closeResult}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            {verificationResult && (
              <ScrollView>
                {verificationResult.valid ? (
                  <View style={styles.validResult}>
                    <Icon name="check-circle" size={60} color="#28a745" />
                    <Text style={styles.resultTitle}>Valid SAFA Member</Text>
                    
                    <View style={styles.memberCard}>
                      <Text style={styles.memberName}>
                        {verificationResult.name}
                      </Text>
                      <Text style={styles.memberInfo}>
                        SAFA ID: {verificationResult.safa_id}
                      </Text>
                      <Text style={styles.memberInfo}>
                        Card: {verificationResult.card_number}
                      </Text>
                      <Text style={styles.memberInfo}>
                        Status: {verificationResult.status}
                      </Text>
                      <Text style={styles.memberInfo}>
                        Expires: {new Date(verificationResult.expires).toLocaleDateString()}
                      </Text>
                    </View>
                  </View>
                ) : (
                  <View style={styles.invalidResult}>
                    <Icon name="error" size={60} color="#dc3545" />
                    <Text style={styles.resultTitle}>Invalid or Expired</Text>
                    <Text style={styles.errorMessage}>
                      {verificationResult.reason || verificationResult.error}
                    </Text>
                  </View>
                )}
                
                <TouchableOpacity style={styles.closeButton} onPress={closeResult}>
                  <Text style={styles.closeButtonText}>Close</Text>
                </TouchableOpacity>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
    marginTop: 20,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 40,
  },
  scanButton: {
    backgroundColor: '#FFD700',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  scanButtonText: {
    color: '#000',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  scannerContainer: {
    flex: 1,
  },
  centerText: {
    flex: 1,
    fontSize: 18,
    padding: 32,
    color: '#777',
  },
  textBold: {
    fontWeight: '500',
    color: '#000',
  },
  buttonText: {
    fontSize: 21,
    color: '#FFD700',
  },
  buttonTouchable: {
    padding: 16,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    margin: 20,
    maxHeight: '80%',
    width: '90%',
  },
  validResult: {
    alignItems: 'center',
  },
  invalidResult: {
    alignItems: 'center',
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 15,
    marginBottom: 20,
  },
  memberCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    width: '100%',
    marginBottom: 20,
  },
  memberName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  memberInfo: {
    fontSize: 14,
    marginBottom: 5,
  },
  errorMessage: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  closeButton: {
    backgroundColor: '#FFD700',
    padding: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
