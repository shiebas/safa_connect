import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  TouchableOpacity,
  Share,
  Dimensions
} from 'react-native';
import QRCode from 'react-native-qrcode-svg';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { CardService } from '../services/CardService';
import { StorageService } from '../services/StorageService';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width - 40;

export default function CardScreen() {
  const [cardData, setCardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    loadCardData();
  }, []);

  const loadCardData = async () => {
    try {
      setLoading(true);
      
      // Load from cache first for offline support
      const cachedCard = await StorageService.getCardData();
      const cachedUser = await StorageService.getUserData();
      
      if (cachedCard && cachedUser) {
        setCardData(cachedCard);
        setUser(cachedUser);
      }
      
      // Try to sync with server
      const freshData = await CardService.getMyCard();
      if (freshData) {
        setCardData(freshData.card);
        setUser(freshData.user);
        
        // Cache for offline use
        await StorageService.saveCardData(freshData.card);
        await StorageService.saveUserData(freshData.user);
      }
      
    } catch (error) {
      console.log('Card load error:', error);
      if (!cardData) {
        Alert.alert('Error', 'Unable to load card data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out my SAFA membership card: ${cardData.card_number}`,
        title: 'My SAFA Card'
      });
    } catch (error) {
      console.log('Share error:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': return '#28a745';
      case 'suspended': return '#dc3545';
      case 'expired': return '#6c757d';
      default: return '#6c757d';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text>Loading your SAFA card...</Text>
      </View>
    );
  }

  if (!cardData || !user) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="error" size={60} color="#dc3545" />
        <Text style={styles.errorText}>Card not available</Text>
        <Text style={styles.errorSubtext}>
          Contact SAFA administration for assistance
        </Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadCardData}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.cardContainer}>
        <LinearGradient
          colors={['#FFD700', '#FFA500']}
          style={styles.card}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          {/* Card Header */}
          <View style={styles.cardHeader}>
            <Text style={styles.safaTitle}>SOUTH AFRICAN</Text>
            <Text style={styles.safaTitle}>FOOTBALL ASSOCIATION</Text>
            <Text style={styles.cardSubtitle}>DIGITAL MEMBERSHIP CARD</Text>
          </View>

          {/* Member Info */}
          <View style={styles.memberSection}>
            <View style={styles.memberInfo}>
              <Text style={styles.memberName}>
                {user.name} {user.surname}
              </Text>
              <Text style={styles.memberDetail}>
                SAFA ID: {user.safa_id}
              </Text>
              <Text style={styles.memberDetail}>
                Role: {user.role_display || user.role}
              </Text>
              <Text style={styles.memberDetail}>
                Member Since: {new Date(user.date_joined).getFullYear()}
              </Text>
            </View>
          </View>

          {/* QR Code Section */}
          <View style={styles.qrSection}>
            <View style={styles.qrContainer}>
              <QRCode
                value={cardData.qr_data}
                size={120}
                backgroundColor="white"
                color="black"
                logo={{
                  uri: 'https://your-domain.com/static/images/default_logo.png'
                }}
                logoSize={30}
                logoBackgroundColor="transparent"
              />
            </View>
            
            <Text style={styles.cardNumber}>{cardData.card_number}</Text>
            
            <View style={[styles.statusBadge, { backgroundColor: getStatusColor(cardData.status) }]}>
              <Text style={styles.statusText}>{cardData.status}</Text>
            </View>
            
            <Text style={styles.validity}>
              Valid until: {new Date(cardData.expires_date).toLocaleDateString()}
            </Text>
          </View>
        </LinearGradient>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
          <Icon name="share" size={20} color="#FFD700" />
          <Text style={styles.actionButtonText}>Share</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton} onPress={loadCardData}>
          <Icon name="refresh" size={20} color="#FFD700" />
          <Text style={styles.actionButtonText}>Refresh</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
    color: '#dc3545',
  },
  errorSubtext: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
    marginTop: 10,
  },
  retryButton: {
    backgroundColor: '#FFD700',
    padding: 12,
    borderRadius: 25,
    marginTop: 20,
  },
  retryButtonText: {
    color: '#000',
    fontWeight: 'bold',
  },
  cardContainer: {
    padding: 20,
    alignItems: 'center',
  },
  card: {
    width: CARD_WIDTH,
    borderRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  cardHeader: {
    alignItems: 'center',
    marginBottom: 20,
    borderBottomWidth: 2,
    borderBottomColor: '#000',
    paddingBottom: 15,
  },
  safaTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    textAlign: 'center',
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#000',
    marginTop: 5,
  },
  memberSection: {
    marginBottom: 20,
  },
  memberInfo: {
    alignItems: 'flex-start',
  },
  memberName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 10,
  },
  memberDetail: {
    fontSize: 14,
    color: '#333',
    marginBottom: 5,
  },
  qrSection: {
    alignItems: 'center',
    borderTopWidth: 2,
    borderTopColor: '#000',
    paddingTop: 20,
  },
  qrContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 5,
  },
  cardNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
    fontFamily: 'monospace',
    letterSpacing: 2,
    marginBottom: 10,
  },
  statusBadge: {
    paddingHorizontal: 15,
    paddingVertical: 5,
    borderRadius: 20,
    marginBottom: 10,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  validity: {
    fontSize: 12,
    color: '#333',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
  },
  actionButton: {
    backgroundColor: '#000',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
  },
  actionButtonText: {
    color: '#FFD700',
    fontWeight: 'bold',
    marginLeft: 8,
  },
});
