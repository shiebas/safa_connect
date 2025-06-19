import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  Animated,
  Dimensions,
  Image,
  Platform,
  ScrollView,
  Share,
  Alert
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ApiService from '../services/api';
import QRCode from 'react-native-qrcode-svg';
import * as Sharing from 'expo-sharing';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width * 0.85;
const CARD_HEIGHT = CARD_WIDTH * 0.63; // Standard card aspect ratio

const DigitalCardScreen = ({ navigation }) => {
  const [cardData, setCardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFlipped, setIsFlipped] = useState(false);
  const [qrData, setQrData] = useState(null);
  
  // Animation values
  const flipAnimation = useRef(new Animated.Value(0)).current;
  const rotateY = flipAnimation.interpolate({
    inputRange: [0, 180],
    outputRange: ['0deg', '180deg'],
  });
  const rotateYFront = flipAnimation.interpolate({
    inputRange: [0, 180],
    outputRange: ['0deg', '180deg'],
  });
  const rotateYBack = flipAnimation.interpolate({
    inputRange: [0, 180],
    outputRange: ['180deg', '0deg'],
  });

  // Shimmer animation
  const shimmerValue = useRef(new Animated.Value(0)).current;
  const shimmer = shimmerValue.interpolate({
    inputRange: [0, 1],
    outputRange: [-width, width],
  });

  useEffect(() => {
    loadCardData();
    startShimmerAnimation();
  }, []);

  const startShimmerAnimation = () => {
    Animated.loop(
      Animated.timing(shimmerValue, {
        toValue: 1,
        duration: 1500,
        useNativeDriver: true,
      })
    ).start();
  };

  const loadCardData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Get digital card data
      const cardResponse = await ApiService.getDigitalCard();
      setCardData(cardResponse);
      
      // Get QR code data
      const qrResponse = await ApiService.getCardQR();
      setQrData(qrResponse);
    } catch (err) {
      console.error('Failed to load card data:', err);
      setError('Failed to load your digital card. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const flipCard = () => {
    Animated.spring(flipAnimation, {
      toValue: isFlipped ? 0 : 180,
      friction: 8,
      tension: 10,
      useNativeDriver: true,
    }).start();
    setIsFlipped(!isFlipped);
  };

  const handleAddToWallet = async () => {
    // In a real implementation, navigate to the appropriate wallet based on platform
    try {
      if (Platform.OS === 'ios') {
        Alert.alert('Add to Apple Wallet', 'Apple Wallet integration coming soon');
      } else {
        // Android - open Google Wallet
        Alert.alert('Add to Google Wallet', 'Would you like to add this card to Google Wallet?', [
          {
            text: 'Cancel',
            style: 'cancel',
          },
          {
            text: 'Add to Google Wallet',
            onPress: () => {
              // This would be replaced with actual Google Wallet integration
              Alert.alert('Google Wallet', 'Google Wallet integration demo - card added successfully');
            },
          },
        ]);
      }
    } catch (err) {
      console.error('Add to wallet error:', err);
      Alert.alert('Error', 'Failed to add card to wallet');
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `My SAFA Digital Membership Card\nMember: ${cardData?.user_name}\nCard #: ${cardData?.card_number}`,
        title: 'SAFA Digital Card',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share card');
    }
  };

  const renderLoading = () => (
    <View style={styles.loadingContainer}>
      <LinearGradient
        colors={['#004d33', '#006633', '#008033']}
        style={[styles.card]}
      >
        <Animated.View 
          style={[
            StyleSheet.absoluteFill,
            {
              backgroundColor: '#ffffff20',
              transform: [{ translateX: shimmer }],
            },
          ]}
        />
        <View style={styles.cardContent}>
          <View style={styles.shimmerLine} />
          <View style={styles.shimmerLine} />
          <View style={styles.shimmerLine} />
        </View>
      </LinearGradient>
      <Text style={styles.loadingText}>Loading your digital card...</Text>
    </View>
  );

  const renderFrontCard = () => {
    if (!cardData) return null;
    
    // Format card number with spaces for readability (4-4-4-4 format)
    const formattedCardNumber = cardData.card_number
      .match(/.{1,4}/g)
      .join(' ');
      
    const expiryDate = new Date(cardData.expires_date);
    const month = String(expiryDate.getMonth() + 1).padStart(2, '0');
    const year = String(expiryDate.getFullYear()).slice(-2);
    
    return (
      <Animated.View 
        style={[
          styles.cardFace,
          {
            transform: [
              { rotateY: rotateYFront },
            ],
            opacity: isFlipped ? 0 : 1,
            zIndex: isFlipped ? 0 : 1,
          }
        ]}
      >
        <LinearGradient
          colors={['#004d33', '#006633', '#008033']}
          style={styles.gradientBackground}
        >
          <View style={styles.cardHeader}>
            <Image 
              source={require('../../assets/safa_logo_small.png')} 
              style={styles.logo} 
              resizeMode="contain"
            />
            <View style={styles.chipContainer}>
              <MaterialCommunityIcons name="integrated-circuit-chip" size={40} color="#FFD700" />
            </View>
          </View>
          
          <View style={styles.cardNumber}>
            <Text style={styles.cardNumberText}>{formattedCardNumber}</Text>
          </View>
          
          <View style={styles.cardFooter}>
            <View style={styles.cardHolderInfo}>
              <Text style={styles.cardLabel}>CARD HOLDER</Text>
              <Text style={styles.cardHolderName}>{cardData.user_name}</Text>
              <Text style={styles.cardLabel}>SAFA ID</Text>
              <Text style={styles.cardSafaId}>{cardData.user_safa_id}</Text>
            </View>
            
            <View style={styles.expiryContainer}>
              <Text style={styles.cardLabel}>VALID THRU</Text>
              <Text style={styles.expiryText}>{`${month}/${year}`}</Text>
              <View style={[styles.statusBadge, { backgroundColor: getStatusColor(cardData.status) }]}>
                <Text style={styles.statusText}>{cardData.status}</Text>
              </View>
            </View>
          </View>
        </LinearGradient>
      </Animated.View>
    );
  };

  const renderBackCard = () => {
    if (!cardData || !qrData) return null;
    
    return (
      <Animated.View 
        style={[
          styles.cardFace,
          styles.cardBack,
          {
            transform: [
              { rotateY: rotateYBack },
            ],
            opacity: isFlipped ? 1 : 0,
            zIndex: isFlipped ? 1 : 0,
          }
        ]}
      >
        <LinearGradient
          colors={['#004d33', '#006633', '#008033']}
          style={styles.gradientBackground}
        >
          <View style={styles.magneticStripe} />
          
          <View style={styles.backContent}>
            <View style={styles.qrContainer}>
              <QRCode
                value={qrData.qr_data || 'https://safa.org.za'}
                size={100}
                color="#000"
                backgroundColor="#fff"
              />
            </View>
            
            <View style={styles.backInfoContainer}>
              <Text style={styles.backInfoTitle}>SAFA Membership</Text>
              <Text style={styles.backInfoText}>
                This card remains property of SAFA.
                Present when requested. Scan QR code
                to verify membership status.
              </Text>
              <Text style={styles.backInfoId}>ID: {cardData.user_safa_id}</Text>
            </View>
          </View>
          
          <Text style={styles.termsText}>
            Terms & Conditions Apply
          </Text>
        </LinearGradient>
      </Animated.View>
    );
  };

  const getStatusColor = (status) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return '#28a745';
      case 'SUSPENDED':
        return '#fd7e14';
      case 'EXPIRED':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <MaterialCommunityIcons name="alert-circle-outline" size={50} color="#dc3545" />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.reloadButton} onPress={loadCardData}>
          <Text style={styles.reloadButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.headerContainer}>
        <Text style={styles.headerTitle}>My Digital Card</Text>
        <Text style={styles.headerSubtitle}>Your SAFA membership digital card</Text>
      </View>
      
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.cardContainer}>
          {isLoading ? renderLoading() : (
            <TouchableOpacity activeOpacity={0.9} onPress={flipCard}>
              <View style={styles.cardWrapper}>
                {renderFrontCard()}
                {renderBackCard()}
              </View>
              
              <Text style={styles.flipGuideText}>Tap card to view {isFlipped ? 'front' : 'back'}</Text>
            </TouchableOpacity>
          )}
        </View>
        
        <View style={styles.actionsContainer}>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={handleAddToWallet}
            disabled={isLoading}
          >
            <MaterialCommunityIcons name="wallet" size={24} color="#006633" />
            <Text style={styles.actionButtonText}>Add to Wallet</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={handleShare}
            disabled={isLoading}
          >
            <Ionicons name="share-outline" size={24} color="#006633" />
            <Text style={styles.actionButtonText}>Share Card</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={loadCardData}
            disabled={isLoading}
          >
            <MaterialCommunityIcons name="refresh" size={24} color="#006633" />
            <Text style={styles.actionButtonText}>Refresh</Text>
          </TouchableOpacity>
        </View>
        
        {cardData && (
          <View style={styles.cardInfoContainer}>
            <Text style={styles.cardInfoTitle}>Card Information</Text>
            <View style={styles.cardInfoRow}>
              <Text style={styles.cardInfoLabel}>Status:</Text>
              <Text style={[styles.cardInfoValue, { color: getStatusColor(cardData.status) }]}>
                {cardData.status}
              </Text>
            </View>
            <View style={styles.cardInfoRow}>
              <Text style={styles.cardInfoLabel}>Issued Date:</Text>
              <Text style={styles.cardInfoValue}>{new Date(cardData.issued_date).toLocaleDateString()}</Text>
            </View>
            <View style={styles.cardInfoRow}>
              <Text style={styles.cardInfoLabel}>Expires Date:</Text>
              <Text style={styles.cardInfoValue}>{new Date(cardData.expires_date).toLocaleDateString()}</Text>
            </View>
            <View style={styles.cardInfoRow}>
              <Text style={styles.cardInfoLabel}>Card Number:</Text>
              <Text style={styles.cardInfoValue}>{cardData.card_number}</Text>
            </View>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  headerContainer: {
    backgroundColor: '#006633',
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#eee',
    marginTop: 5,
  },
  scrollContent: {
    paddingBottom: 30,
  },
  cardContainer: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 20,
  },
  cardWrapper: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 5,
    },
    shadowOpacity: 0.34,
    shadowRadius: 6.27,
    elevation: 10,
  },
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: 16,
    overflow: 'hidden',
  },
  cardFace: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backfaceVisibility: 'hidden',
    borderRadius: 16,
    overflow: 'hidden',
  },
  cardBack: {
    transform: [{ rotateY: '180deg' }],
  },
  gradientBackground: {
    width: '100%',
    height: '100%',
    padding: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  logo: {
    width: 60,
    height: 30,
    tintColor: '#FFD700',
  },
  chipContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardNumber: {
    marginBottom: 15,
  },
  cardNumberText: {
    fontSize: 18,
    color: '#fff',
    letterSpacing: 2,
    fontWeight: '500',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 'auto',
  },
  cardHolderInfo: {
    flex: 1,
  },
  cardLabel: {
    fontSize: 8,
    color: '#FFD700',
    marginBottom: 2,
  },
  cardHolderName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
    textTransform: 'uppercase',
  },
  cardSafaId: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  expiryContainer: {
    alignItems: 'flex-end',
  },
  expiryText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    backgroundColor: '#28a745',
  },
  statusText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  magneticStripe: {
    height: 40,
    backgroundColor: '#111',
    marginBottom: 20,
    marginTop: -20,
    marginHorizontal: -20,
  },
  backContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  qrContainer: {
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 8,
  },
  backInfoContainer: {
    flex: 1,
    marginLeft: 15,
  },
  backInfoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 5,
  },
  backInfoText: {
    fontSize: 9,
    color: '#fff',
    marginBottom: 8,
  },
  backInfoId: {
    fontSize: 10,
    color: '#FFD700',
    fontWeight: '500',
  },
  termsText: {
    fontSize: 8,
    color: '#aaa',
    textAlign: 'center',
    marginTop: 'auto',
    fontStyle: 'italic',
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  actionButton: {
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    padding: 10,
    borderRadius: 10,
    width: width / 3.5,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  actionButtonText: {
    color: '#006633',
    marginTop: 5,
    fontSize: 12,
  },
  cardInfoContainer: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    borderRadius: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  cardInfoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  cardInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  cardInfoLabel: {
    color: '#666',
  },
  cardInfoValue: {
    fontWeight: '500',
    color: '#333',
  },
  loadingContainer: {
    alignItems: 'center',
  },
  shimmerLine: {
    height: 15,
    width: '80%',
    backgroundColor: '#ffffff30',
    marginVertical: 10,
    borderRadius: 5,
  },
  cardContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 15,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginVertical: 20,
  },
  reloadButton: {
    backgroundColor: '#006633',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  reloadButtonText: {
    color: '#fff',
    fontWeight: '500',
  },
  flipGuideText: {
    textAlign: 'center',
    color: '#666',
    marginTop: 15,
    fontStyle: 'italic',
    fontSize: 12,
  },
});

export default DigitalCardScreen;
