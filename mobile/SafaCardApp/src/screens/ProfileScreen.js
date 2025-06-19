import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  FlatList,
  Image,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { MaterialCommunityIcons, Ionicons, MaterialIcons } from '@expo/vector-icons';
import ApiService from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const ProfileScreen = ({ navigation }) => {
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const profileData = await ApiService.getUserProfile();
      setUserProfile(profileData);
    } catch (err) {
      console.error('Failed to load profile:', err);
      setError('Failed to load profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout Confirmation',
      'Are you sure you want to log out?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          onPress: async () => {
            try {
              await ApiService.logout();
              navigation.reset({
                index: 0,
                routes: [{ name: 'Login' }],
              });
            } catch (err) {
              console.error('Logout error:', err);
              Alert.alert('Logout Error', 'Failed to log out. Please try again.');
            }
          },
        },
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#006633" />
        <Text style={styles.loadingText}>Loading profile...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <MaterialCommunityIcons name="account-alert" size={50} color="#dc3545" />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.reloadButton} onPress={loadUserProfile}>
          <Text style={styles.reloadButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      
      <LinearGradient
        colors={['#004d33', '#006633']}
        style={styles.headerBackground}
      >
        <View style={styles.profileHeader}>
          <View style={styles.profileImageContainer}>
            {userProfile?.profile_photo ? (
              <Image 
                source={{ uri: userProfile.profile_photo }} 
                style={styles.profileImage} 
              />
            ) : (
              <View style={[styles.profileImage, styles.profileImagePlaceholder]}>
                <Text style={styles.profileInitials}>
                  {userProfile?.first_name?.[0] || ''}{userProfile?.last_name?.[0] || ''}
                </Text>
              </View>
            )}
          </View>
          <Text style={styles.userName}>{userProfile?.first_name} {userProfile?.last_name}</Text>
          <Text style={styles.userEmail}>{userProfile?.email}</Text>
          <Text style={styles.userSafaId}>SAFA ID: {userProfile?.safa_id}</Text>
        </View>
      </LinearGradient>
      
      <ScrollView style={styles.contentContainer}>
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Personal Information</Text>
          
          <View style={styles.infoItem}>
            <MaterialIcons name="person" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Full Name</Text>
              <Text style={styles.infoValue}>{userProfile?.first_name} {userProfile?.last_name}</Text>
            </View>
          </View>
          
          <View style={styles.infoItem}>
            <MaterialIcons name="email" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Email</Text>
              <Text style={styles.infoValue}>{userProfile?.email}</Text>
            </View>
          </View>
          
          <View style={styles.infoItem}>
            <MaterialIcons name="phone" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Phone</Text>
              <Text style={styles.infoValue}>{userProfile?.phone || 'Not provided'}</Text>
            </View>
          </View>
          
          <View style={styles.infoItem}>
            <MaterialIcons name="location-on" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Region</Text>
              <Text style={styles.infoValue}>{userProfile?.region || 'Not specified'}</Text>
            </View>
          </View>
        </View>
        
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Membership Information</Text>
          
          <View style={styles.infoItem}>
            <MaterialCommunityIcons name="card-account-details" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Membership Type</Text>
              <Text style={styles.infoValue}>{userProfile?.membership_type || 'Standard'}</Text>
            </View>
          </View>
          
          <View style={styles.infoItem}>
            <MaterialCommunityIcons name="calendar" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Member Since</Text>
              <Text style={styles.infoValue}>
                {userProfile?.member_since 
                  ? new Date(userProfile.member_since).toLocaleDateString() 
                  : 'Not available'}
              </Text>
            </View>
          </View>
          
          <View style={styles.infoItem}>
            <MaterialCommunityIcons name="calendar-clock" size={20} color="#006633" style={styles.infoIcon} />
            <View style={styles.infoContent}>
              <Text style={styles.infoLabel}>Membership Expiry</Text>
              <Text style={styles.infoValue}>
                {userProfile?.membership_expiry 
                  ? new Date(userProfile.membership_expiry).toLocaleDateString() 
                  : 'Not available'}
              </Text>
            </View>
          </View>
          
          {userProfile?.club_name && (
            <View style={styles.infoItem}>
              <MaterialCommunityIcons name="shield" size={20} color="#006633" style={styles.infoIcon} />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Club Affiliation</Text>
                <Text style={styles.infoValue}>{userProfile.club_name}</Text>
              </View>
            </View>
          )}
        </View>
        
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.actionButton} onPress={() => navigation.navigate('DigitalCard')}>
            <MaterialCommunityIcons name="card-account-details-outline" size={24} color="#006633" />
            <Text style={styles.actionButtonText}>View Digital Card</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.actionButton} onPress={handleLogout}>
            <MaterialIcons name="logout" size={24} color="#dc3545" />
            <Text style={[styles.actionButtonText, { color: '#dc3545' }]}>Logout</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>SAFA Digital Card App v1.0.0</Text>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
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
  headerBackground: {
    paddingTop: 60,
    paddingBottom: 30,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  profileHeader: {
    alignItems: 'center',
  },
  profileImageContainer: {
    marginBottom: 15,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: '#FFD700',
  },
  profileImagePlaceholder: {
    backgroundColor: '#004d33',
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileInitials: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  userName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  userEmail: {
    fontSize: 14,
    color: '#ddd',
    marginTop: 5,
  },
  userSafaId: {
    fontSize: 14,
    color: '#FFD700',
    marginTop: 5,
    fontWeight: '500',
  },
  contentContainer: {
    flex: 1,
    padding: 20,
  },
  sectionContainer: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  infoItem: {
    flexDirection: 'row',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  infoIcon: {
    marginTop: 2,
    marginRight: 15,
  },
  infoContent: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
    marginTop: 2,
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    marginBottom: 20,
  },
  actionButton: {
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingVertical: 15,
    paddingHorizontal: 10,
    alignItems: 'center',
    width: '48%',
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
    marginTop: 5,
    fontWeight: '500',
    color: '#006633',
  },
  versionContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  versionText: {
    color: '#999',
    fontSize: 12,
  },
});

export default ProfileScreen;
