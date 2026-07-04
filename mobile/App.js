import { useState } from "react";
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import * as ImagePicker from "expo-image-picker";
import { BACKEND_URL } from "./config";

// A sensible demo profile — editable on screen.
const DEFAULT_PROFILE = {
  name: "Rekha Das",
  age: "42",
  gender: "female",
  state: "West Bengal",
  occupation: "homemaker",
  documents: "Aadhaar, Swasthya Sathi card, Bank account",
};

export default function App() {
  const [profile, setProfile] = useState(DEFAULT_PROFILE);
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const pick = async (fromCamera) => {
    const perm = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return setError("Permission denied");
    const fn = fromCamera
      ? ImagePicker.launchCameraAsync
      : ImagePicker.launchImageLibraryAsync;
    const res = await fn({ base64: true, quality: 0.5 });
    if (!res.canceled) {
      setImage(res.assets[0]);
      setResult(null);
      setError(null);
    }
  };

  const analyze = async () => {
    if (!image) return setError("Take or pick a document photo first.");
    setLoading(true);
    setError(null);
    try {
      const body = {
        image_b64: image.base64,
        profile: {
          ...profile,
          age: parseInt(profile.age) || null,
          documents: profile.documents.split(",").map((s) => s.trim()),
        },
      };
      const r = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`Server ${r.status}`);
      setResult(await r.json());
    } catch (e) {
      setError(`${e.message} — is the backend running at ${BACKEND_URL}?`);
    } finally {
      setLoading(false);
    }
  };

  const field = (key, label) => (
    <View style={styles.fieldRow} key={key}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        style={styles.input}
        value={String(profile[key])}
        onChangeText={(v) => setProfile((p) => ({ ...p, [key]: v }))}
      />
    </View>
  );

  return (
    <ScrollView style={styles.page} contentContainerStyle={{ padding: 20, paddingTop: 60 }}>
      <StatusBar style="light" />
      <Text style={styles.brand}>সাথী · Saathi</Text>
      <Text style={styles.tag}>আপনার নথি বুঝুন, আপনার অধিকার পান — অফলাইন</Text>

      <Text style={styles.section}>আপনার তথ্য / Your details</Text>
      {field("name", "Name")}
      {field("age", "Age")}
      {field("gender", "Gender")}
      {field("state", "State")}
      {field("occupation", "Occupation")}
      {field("documents", "Documents you have")}

      <Text style={styles.section}>নথির ছবি / Document</Text>
      <View style={styles.row}>
        <TouchableOpacity style={styles.btn} onPress={() => pick(true)}>
          <Text style={styles.btnText}>📷 ছবি তুলুন</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.btn, styles.btnAlt]} onPress={() => pick(false)}>
          <Text style={styles.btnText}>🖼️ গ্যালারি</Text>
        </TouchableOpacity>
      </View>
      {image && <Image source={{ uri: image.uri }} style={styles.preview} />}

      <TouchableOpacity style={styles.cta} onPress={analyze} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.ctaText}>বুঝিয়ে দাও →</Text>}
      </TouchableOpacity>

      {error && <Text style={styles.error}>{error}</Text>}

      {result && (
        <View style={styles.result}>
          {result.document?.doc_type && (
            <Text style={styles.docType}>📄 {result.document.doc_type}</Text>
          )}
          {result.document?.summary_bn && (
            <Text style={styles.summary}>{result.document.summary_bn}</Text>
          )}

          {(result.document?.key_points_bn || []).map((k, i) => (
            <Text key={i} style={styles.bullet}>• {k}</Text>
          ))}

          {result.actions?.length > 0 && (
            <>
              <Text style={styles.section}>ব্যবস্থা / Actions taken</Text>
              {result.actions.map((a, i) => (
                <View key={i} style={styles.action}>
                  <Text style={styles.actionTool}>🛠️ {a.tool}</Text>
                  {a.result?.eligible !== undefined && (
                    <Text style={a.result.eligible ? styles.yes : styles.no}>
                      {a.result.scheme_name}: {a.result.eligible ? "✅ যোগ্য (Eligible)" : "❌ যোগ্য নন"}
                    </Text>
                  )}
                  {a.result?.status === "reminder_set" && (
                    <Text style={styles.yes}>⏰ Reminder: {a.result.title} ({a.result.when})</Text>
                  )}
                  {a.result?.missing_documents && (
                    <Text style={styles.no}>Missing: {a.result.missing_documents.join(", ") || "none"}</Text>
                  )}
                </View>
              ))}
            </>
          )}

          {result.answer_bn ? (
            <>
              <Text style={styles.section}>সাথী বলছে / Saathi says</Text>
              <Text style={styles.answer}>{result.answer_bn}</Text>
            </>
          ) : null}
        </View>
      )}
      <View style={{ height: 60 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: "#0f1020" },
  brand: { fontSize: 34, fontWeight: "800", color: "#fff" },
  tag: { color: "#a9b0d0", marginTop: 4, marginBottom: 16 },
  section: { color: "#8ea2ff", fontWeight: "700", marginTop: 22, marginBottom: 8, fontSize: 15 },
  fieldRow: { marginBottom: 8 },
  fieldLabel: { color: "#a9b0d0", fontSize: 12, marginBottom: 2 },
  input: { backgroundColor: "#1b1d36", color: "#fff", borderRadius: 10, padding: 10 },
  row: { flexDirection: "row", gap: 10 },
  btn: { flex: 1, backgroundColor: "#2a2d55", padding: 14, borderRadius: 12, alignItems: "center" },
  btnAlt: { backgroundColor: "#22243f" },
  btnText: { color: "#fff", fontWeight: "600" },
  preview: { width: "100%", height: 220, borderRadius: 12, marginTop: 12 },
  cta: { backgroundColor: "#5b6cff", padding: 16, borderRadius: 14, alignItems: "center", marginTop: 18 },
  ctaText: { color: "#fff", fontSize: 17, fontWeight: "800" },
  error: { color: "#ff8a8a", marginTop: 14 },
  result: { marginTop: 18 },
  docType: { color: "#ffd479", fontWeight: "700", fontSize: 16 },
  summary: { color: "#fff", fontSize: 17, lineHeight: 26, marginTop: 8 },
  bullet: { color: "#cdd3f0", fontSize: 15, marginTop: 6 },
  action: { backgroundColor: "#161832", padding: 12, borderRadius: 10, marginBottom: 8 },
  actionTool: { color: "#8ea2ff", fontSize: 12, marginBottom: 4 },
  yes: { color: "#7ee0a0", fontWeight: "600" },
  no: { color: "#ff9d9d", fontWeight: "600" },
  answer: { color: "#fff", fontSize: 17, lineHeight: 28, backgroundColor: "#161832", padding: 14, borderRadius: 12 },
});
