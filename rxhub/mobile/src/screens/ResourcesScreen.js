import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import api from '../services/api';

const CATEGORIES = [
  { key: '', label: 'All' },
  { key: 'NEWSLETTER', label: 'Newsletters' },
  { key: 'HEALTH_TIP', label: 'Health Tips' },
  { key: 'DRUG_ALERT', label: 'Drug Alerts' },
  { key: 'SCARCITY_ALERT', label: 'Scarcity' },
  { key: 'PBM_UPDATE', label: 'Updates' },
];

export default function ResourcesScreen() {
  const [resources, setResources] = useState([]);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = { page_size: 30 };
    if (category) params.category = category;

    api.get('/resources', { params })
      .then(({ data }) => setResources(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [category]);

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.category}>{item.category.replace(/_/g, ' ')}</Text>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.body} numberOfLines={4}>{item.body}</Text>
      {item.diagnosis_tags?.length > 0 && (
        <View style={styles.tags}>
          {item.diagnosis_tags.map(t => <View key={t} style={styles.tag}><Text style={styles.tagText}>{t}</Text></View>)}
        </View>
      )}
      <Text style={styles.date}>{item.published_at ? new Date(item.published_at).toLocaleDateString() : ''}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterBar}>
        {CATEGORIES.map(c => (
          <TouchableOpacity
            key={c.key}
            style={[styles.filterBtn, category === c.key && styles.filterBtnActive]}
            onPress={() => setCategory(c.key)}
          >
            <Text style={[styles.filterText, category === c.key && styles.filterTextActive]}>{c.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <FlatList
        data={resources}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        ListEmptyComponent={<Text style={styles.empty}>{loading ? 'Loading...' : 'No resources found'}</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  filterBar: { backgroundColor: '#fff', paddingVertical: 12, paddingHorizontal: 16, maxHeight: 56 },
  filterBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#F0F0F0', marginRight: 8 },
  filterBtnActive: { backgroundColor: '#1A1A2E' },
  filterText: { fontSize: 13, fontWeight: '600', color: '#666' },
  filterTextActive: { color: '#fff' },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 20, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2 },
  category: { fontSize: 11, fontWeight: '700', color: '#E87722', textTransform: 'uppercase' },
  title: { fontSize: 17, fontWeight: '700', color: '#1A1A2E', marginTop: 4 },
  body: { fontSize: 14, color: '#666', lineHeight: 20, marginTop: 8 },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  tag: { backgroundColor: '#F0F0F0', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  tagText: { fontSize: 11, color: '#444' },
  date: { fontSize: 12, color: '#999', marginTop: 8 },
  empty: { textAlign: 'center', color: '#999', marginTop: 60 },
});
