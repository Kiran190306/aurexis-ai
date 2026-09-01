/**
 * Voice Intelligence Page
 * Main page for voice interactions, transcription, synthesis, and voice chat.
 */
import { useState, useRef, useEffect } from 'react'
import { useVoiceHistory, useVoiceSettings, useUpdateVoiceSettings } from '../services/voice-hooks'
import { Mic, MicOff, Volume2, Settings, History, Loader2, Play, Square } from 'lucide-react'

type TabType = 'chat' | 'transcribe' | 'speak' | 'history' | 'settings'

export default function VoicePage() {
  const [activeTab, setActiveTab] = useState<TabType>('chat')
  const { data: history, isLoading: historyLoading } = useVoiceHistory()
  const { data: settings, isLoading: settingsLoading } = useVoiceSettings()
  const updateSettings = useUpdateVoiceSettings()
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Voice Intelligence</h1>
        <p className="mt-2 text-muted-foreground">Natural voice communication with Jarvis AI</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        <TabButton active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} icon={<Mic />}>
          Voice Chat
        </TabButton>
        <TabButton active={activeTab === 'transcribe'} onClick={() => setActiveTab('transcribe')} icon={<Mic />}>
          Transcribe
        </TabButton>
        <TabButton active={activeTab === 'speak'} onClick={() => setActiveTab('speak')} icon={<Volume2 />}>
          Speak
        </TabButton>
        <TabButton active={activeTab === 'history'} onClick={() => setActiveTab('history')} icon={<History />}>
          History
        </TabButton>
        <TabButton active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} icon={<Settings />}>
          Settings
        </TabButton>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'chat' && <VoiceChatTab settings={settings} />}
        {activeTab === 'transcribe' && <TranscribeTab />}
        {activeTab === 'speak' && <SpeakTab settings={settings} />}
        {activeTab === 'history' && <HistoryTab history={history} isLoading={historyLoading} />}
        {activeTab === 'settings' && <SettingsTab settings={settings} updateSettings={updateSettings} isLoading={settingsLoading} />}
      </div>
    </div>
  )
}

function TabButton({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
        active
          ? 'border-primary text-foreground'
          : 'border-transparent text-muted-foreground hover:text-foreground'
      }`}
    >
      {icon}
      {children}
    </button>
  )
}

function VoiceChatTab({ settings }: { settings: any }) {
  const [isRecording, setIsRecording] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' })
        
        // Send to API
        const { useVoiceChat } = await import('../services/voice-hooks')
        const voiceChat = useVoiceChat()
        
        await voiceChat.mutateAsync({
          file: audioFile,
          request: {
            conversation_id: conversationId || undefined,
            voice: settings?.voice_profile,
            mode: 'push_to_talk'
          }
        })
      }
      
      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Failed to start recording:', error)
    }
  }
  
  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }
  
  const playResponse = () => {
    // In production, play the audio response
    setIsSpeaking(true)
    setTimeout(() => setIsSpeaking(false), 3000)
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors ${
            isRecording
              ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          {isRecording ? <Square className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
        </button>
      </div>
      
      <div className="bg-card border border-border rounded-lg p-6 space-y-4">
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Your Message</h3>
          <p className="text-foreground min-h-[60px]">{transcript || 'Press the microphone button to speak...'}</p>
        </div>
        
        <div className="border-t border-border pt-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-muted-foreground">Jarvis Response</h3>
            {response && (
              <button
                onClick={playResponse}
                className="flex items-center gap-2 text-sm text-primary hover:text-primary/90"
              >
                <Play className="h-4 w-4" />
                Play
              </button>
            )}
          </div>
          <p className="text-foreground min-h-[60px] mt-2">{response || 'Waiting for your input...'}</p>
        </div>
      </div>
      
      <WaveformVisualization isActive={isRecording} />
    </div>
  )
}

function TranscribeTab() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const handleTranscribe = async () => {
    if (!selectedFile) return
    
    setIsProcessing(true)
    try {
      const { useTranscribe } = await import('../services/voice-hooks')
      const transcribe = useTranscribe()
      
      const response = await transcribe.mutateAsync({
        file: selectedFile,
        request: { detect_language: true }
      })
      
      setResult(response)
    } catch (error) {
      console.error('Transcription failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }
  
  return (
    <div className="space-y-6">
      <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => e.target.files && setSelectedFile(e.target.files[0])}
          className="hidden"
          id="audio-upload"
        />
        <label htmlFor="audio-upload" className="cursor-pointer">
          <Mic className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-foreground font-medium">Upload Audio File</p>
          <p className="text-sm text-muted-foreground mt-1">WAV, MP3, OGG, FLAC</p>
        </label>
      </div>
      
      {selectedFile && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg">
            <Mic className="h-5 w-5 text-muted-foreground" />
            <span className="text-foreground">{selectedFile.name}</span>
          </div>
          
          <button
            onClick={handleTranscribe}
            disabled={isProcessing}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
            Transcribe
          </button>
        </div>
      )}
      
      {result && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Transcription Result</h3>
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Transcribed Text</h4>
              <p className="text-foreground">{result.text}</p>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Language:</span>
                <span className="text-foreground">{result.language || 'auto-detected'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Confidence:</span>
                <span className="text-foreground">{(result.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Duration:</span>
                <span className="text-foreground">{result.duration.toFixed(1)}s</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SpeakTab({ settings }: { settings: any }) {
  const [text, setText] = useState('')
  const [voice, setVoice] = useState(settings?.voice_profile || 'en_US-amy-medium')
  const [speed, setSpeed] = useState(settings?.speed || 1.0)
  const [pitch, setPitch] = useState(settings?.pitch || 1.0)
  const [isSpeaking, setIsSpeaking] = useState(false)
  
  const handleSpeak = async () => {
    if (!text) return
    
    setIsSpeaking(true)
    try {
      const { useSynthesize } = await import('../services/voice-hooks')
      const synthesize = useSynthesize()
      
      const response = await synthesize.mutateAsync({
        text,
        voice,
        speed,
        pitch,
        format: 'wav'
      })
      
      // Play audio
      const audioData = new Uint8Array(response.audio_data.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16)))
      const audioBlob = new Blob([audioData], { type: 'audio/wav' })
      const audioUrl = URL.createObjectURL(audioBlob)
      
      const audio = new Audio(audioUrl)
      audio.onended = () => {
        setIsSpeaking(false)
        URL.revokeObjectURL(audioUrl)
      }
      audio.play()
    } catch (error) {
      console.error('Synthesis failed:', error)
      setIsSpeaking(false)
    }
  }
  
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">Text to Speak</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to synthesize..."
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground min-h-[120px]"
        />
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">Voice</label>
          <select
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          >
            <option value="en_US-amy-medium">Amy (Female, US)</option>
            <option value="en_US-dave-medium">Dave (Male, US)</option>
            <option value="en_GB-emma-medium">Emma (Female, UK)</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">Speed: {speed.toFixed(1)}x</label>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">Pitch: {pitch.toFixed(1)}x</label>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={pitch}
            onChange={(e) => setPitch(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
      </div>
      
      <button
        onClick={handleSpeak}
        disabled={!text || isSpeaking}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
      >
        {isSpeaking ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Volume2 className="h-4 w-4" />
        )}
        Speak
      </button>
    </div>
  )
}

function HistoryTab({ history, isLoading }: { history: any[] | undefined; isLoading: boolean }) {
  return (
    <div className="space-y-4">
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : !history || history.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No voice conversations yet
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div key={item.uuid} className="p-4 bg-card border border-border rounded-lg">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium text-foreground capitalize">{item.mode.replace('_', ' ')}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {new Date(item.started_at).toLocaleString()}
                  </p>
                </div>
                <div className={`flex items-center gap-1 text-sm ${
                  item.status === 'active' ? 'text-green-500' : 'text-muted-foreground'
                }`}>
                  {item.status}
                </div>
              </div>
              <div className="mt-3 flex items-center gap-4 text-sm text-muted-foreground">
                <span>{item.message_count} messages</span>
                <span>{item.total_audio_duration.toFixed(1)}s audio</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SettingsTab({ settings, updateSettings, isLoading }: { settings: any; updateSettings: any; isLoading: boolean }) {
  const [localSettings, setLocalSettings] = useState(settings || {})
  
  useEffect(() => {
    if (settings) {
      setLocalSettings(settings)
    }
  }, [settings])
  
  const handleSave = async () => {
    await updateSettings.mutateAsync(localSettings)
  }
  
  return (
    <div className="space-y-6">
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Text-to-Speech</h3>
            
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Voice Profile</label>
              <select
                value={localSettings.voice_profile || ''}
                onChange={(e) => setLocalSettings({ ...localSettings, voice_profile: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              >
                <option value="en_US-amy-medium">Amy (Female, US)</option>
                <option value="en_US-dave-medium">Dave (Male, US)</option>
                <option value="en_GB-emma-medium">Emma (Female, UK)</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Speed: {(localSettings.speed || 1.0).toFixed(1)}x</label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={localSettings.speed || 1.0}
                  onChange={(e) => setLocalSettings({ ...localSettings, speed: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Pitch: {(localSettings.pitch || 1.0).toFixed(1)}x</label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={localSettings.pitch || 1.0}
                  onChange={(e) => setLocalSettings({ ...localSettings, pitch: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          </div>
          
          <div className="space-y-4 pt-4 border-t border-border">
            <h3 className="text-lg font-semibold text-foreground">Speech-to-Text</h3>
            
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Language</label>
              <select
                value={localSettings.language || 'en'}
                onChange={(e) => setLocalSettings({ ...localSettings, language: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
              </select>
            </div>
            
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={localSettings.detect_language || false}
                onChange={(e) => setLocalSettings({ ...localSettings, detect_language: e.target.checked })}
                className="rounded"
              />
              <span className="text-foreground">Auto-detect language</span>
            </label>
          </div>
          
          <div className="space-y-4 pt-4 border-t border-border">
            <h3 className="text-lg font-semibold text-foreground">Wake Word</h3>
            
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={localSettings.wake_word_enabled || false}
                onChange={(e) => setLocalSettings({ ...localSettings, wake_word_enabled: e.target.checked })}
                className="rounded"
              />
              <span className="text-foreground">Enable wake word detection</span>
            </label>
            
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Wake Phrase</label>
              <input
                type="text"
                value={localSettings.wake_word_phrase || 'hey jarvis'}
                onChange={(e) => setLocalSettings({ ...localSettings, wake_word_phrase: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Sensitivity: {(localSettings.wake_word_sensitivity || 0.5).toFixed(1)}</label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.1"
                value={localSettings.wake_word_sensitivity || 0.5}
                onChange={(e) => setLocalSettings({ ...localSettings, wake_word_sensitivity: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>
          
          <div className="space-y-4 pt-4 border-t border-border">
            <h3 className="text-lg font-semibold text-foreground">Privacy</h3>
            
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={localSettings.save_recordings || false}
                onChange={(e) => setLocalSettings({ ...localSettings, save_recordings: e.target.checked })}
                className="rounded"
              />
              <span className="text-foreground">Save audio recordings</span>
            </label>
            
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={localSettings.auto_transcribe !== false}
                onChange={(e) => setLocalSettings({ ...localSettings, auto_transcribe: e.target.checked })}
                className="rounded"
              />
              <span className="text-foreground">Auto-transcribe voice input</span>
            </label>
          </div>
          
          <button
            onClick={handleSave}
            disabled={updateSettings.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {updateSettings.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Settings className="h-4 w-4" />
            )}
            Save Settings
          </button>
        </>
      )}
    </div>
  )
}

function WaveformVisualization({ isActive }: { isActive: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  useEffect(() => {
    if (!isActive) return
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const animate = () => {
      if (!isActive) return
      
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      ctx.strokeStyle = '#3b82f6'
      ctx.lineWidth = 2
      
      ctx.beginPath()
      for (let i = 0; i < canvas.width; i++) {
        const amplitude = Math.random() * 50
        const y = canvas.height / 2 + Math.sin(i * 0.05 + Date.now() * 0.01) * amplitude
        if (i === 0) {
          ctx.moveTo(i, y)
        } else {
          ctx.lineTo(i, y)
        }
      }
      ctx.stroke()
      
      requestAnimationFrame(animate)
    }
    
    animate()
  }, [isActive])
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <canvas
        ref={canvasRef}
        width={400}
        height={100}
        className="w-full h-24"
      />
    </div>
  )
}
