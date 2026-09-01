/**
 * Vision Intelligence Page
 * Main page for image analysis, OCR, screenshot understanding, and document processing.
 */
import { useState } from 'react'
import { useVisionHistory, useAnalyzeImage, usePerformOCR, useAnalyzeScreenshot, useProcessDocument } from '../services/vision-hooks'
import { Upload, Image as ImageIcon, FileText, Scan, Camera, History, Loader2, CheckCircle, XCircle } from 'lucide-react'

type TabType = 'analyze' | 'ocr' | 'screenshot' | 'document' | 'history'

export default function VisionPage() {
  const [activeTab, setActiveTab] = useState<TabType>('analyze')
  const { data: history, isLoading: historyLoading } = useVisionHistory()
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Vision Intelligence</h1>
        <p className="mt-2 text-muted-foreground">Analyze images, extract text, understand screenshots, and process documents</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        <TabButton active={activeTab === 'analyze'} onClick={() => setActiveTab('analyze')} icon={<ImageIcon />}>
          Analyze Image
        </TabButton>
        <TabButton active={activeTab === 'ocr'} onClick={() => setActiveTab('ocr')} icon={<Scan />}>
          OCR
        </TabButton>
        <TabButton active={activeTab === 'screenshot'} onClick={() => setActiveTab('screenshot')} icon={<Camera />}>
          Screenshot
        </TabButton>
        <TabButton active={activeTab === 'document'} onClick={() => setActiveTab('document')} icon={<FileText />}>
          Document
        </TabButton>
        <TabButton active={activeTab === 'history'} onClick={() => setActiveTab('history')} icon={<History />}>
          History
        </TabButton>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'analyze' && <ImageAnalyzeTab />}
        {activeTab === 'ocr' && <OCRTab />}
        {activeTab === 'screenshot' && <ScreenshotTab />}
        {activeTab === 'document' && <DocumentTab />}
        {activeTab === 'history' && <HistoryTab history={history} isLoading={historyLoading} />}
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

function ImageAnalyzeTab() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [taskTypes, setTaskTypes] = useState<string[]>(['image_captioning'])
  const analyzeImage = useAnalyzeImage()
  const [result, setResult] = useState<any>(null)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setResult(null)
  }

  const handleAnalyze = async () => {
    if (!selectedFile) return
    
    try {
      const response = await analyzeImage.mutateAsync({
        file: selectedFile,
        request: { task_types: taskTypes }
      })
      setResult(response)
    } catch (error) {
      console.error('Analysis failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      <ImageUpload onFileSelect={handleFileSelect} />
      
      {selectedFile && (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Analysis Options</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                { value: 'image_captioning', label: 'Image Captioning' },
                { value: 'object_detection', label: 'Object Detection' },
                { value: 'scene_understanding', label: 'Scene Understanding' },
                { value: 'chart_analysis', label: 'Chart Analysis' },
                { value: 'table_extraction', label: 'Table Extraction' },
              ].map((option) => (
                <label key={option.value} className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg border border-border cursor-pointer hover:bg-muted/50">
                  <input
                    type="checkbox"
                    checked={taskTypes.includes(option.value)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setTaskTypes([...taskTypes, option.value])
                      } else {
                        setTaskTypes(taskTypes.filter(t => t !== option.value))
                      }
                    }}
                    className="rounded"
                  />
                  <span className="text-sm text-foreground">{option.label}</span>
                </label>
              ))}
            </div>
          </div>
          
          <button
            onClick={handleAnalyze}
            disabled={analyzeImage.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {analyzeImage.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Scan className="h-4 w-4" />
            )}
            Analyze Image
          </button>
        </div>
      )}
      
      {result && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Analysis Results</h3>
          <div className="space-y-4">
            {result.caption && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Caption</h4>
                <p className="text-foreground">{result.caption}</p>
              </div>
            )}
            {result.objects_detected && result.objects_detected.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Detected Objects</h4>
                <BoundingBoxOverlay objects={result.objects_detected} />
              </div>
            )}
            {result.scene_description && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Scene Description</h4>
                <p className="text-foreground">{result.scene_description}</p>
              </div>
            )}
            <ConfidenceScores
              overall={result.overall_confidence}
              processingTime={result.processing_time_seconds}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function OCRTab() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [language, setLanguage] = useState<string>('eng')
  const [preserveLayout, setPreserveLayout] = useState(true)
  const performOCR = usePerformOCR()
  const [result, setResult] = useState<any>(null)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setResult(null)
  }

  const handleOCR = async () => {
    if (!selectedFile) return
    
    try {
      const response = await performOCR.mutateAsync({
        file: selectedFile,
        request: { language, preserve_layout }
      })
      setResult(response)
    } catch (error) {
      console.error('OCR failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      <ImageUpload onFileSelect={handleFileSelect} />
      
      {selectedFile && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
              >
                <option value="eng">English</option>
                <option value="fra">French</option>
                <option value="deu">German</option>
                <option value="spa">Spanish</option>
                <option value="ita">Italian</option>
                <option value="por">Portuguese</option>
                <option value="chi_sim">Chinese (Simplified)</option>
                <option value="jpn">Japanese</option>
              </select>
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="preserveLayout"
                checked={preserveLayout}
                onChange={(e) => setPreserveLayout(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="preserveLayout" className="text-sm text-foreground">Preserve Layout</label>
            </div>
          </div>
          
          <button
            onClick={handleOCR}
            disabled={performOCR.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {performOCR.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Scan className="h-4 w-4" />
            )}
            Extract Text
          </button>
        </div>
      )}
      
      {result && (
        <OCRViewer result={result} />
      )}
    </div>
  )
}

function ScreenshotTab() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const analyzeScreenshot = useAnalyzeScreenshot()
  const [result, setResult] = useState<any>(null)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setResult(null)
  }

  const handleAnalyze = async () => {
    if (!selectedFile) return
    
    try {
      const response = await analyzeScreenshot.mutateAsync({
        file: selectedFile,
        request: { detect_ui_elements: true, detect_errors: true }
      })
      setResult(response)
    } catch (error) {
      console.error('Screenshot analysis failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      <ScreenshotUpload onFileSelect={handleFileSelect} />
      
      {selectedFile && (
        <button
          onClick={handleAnalyze}
          disabled={analyzeScreenshot.isPending}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {analyzeScreenshot.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Camera className="h-4 w-4" />
          )}
          Analyze Screenshot
        </button>
      )}
      
      {result && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Screenshot Analysis</h3>
          <div className="space-y-4">
            {result.window_title && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Window Title</h4>
                <p className="text-foreground">{result.window_title}</p>
              </div>
            )}
            {result.application_type && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Application Type</h4>
                <p className="text-foreground capitalize">{result.application_type}</p>
              </div>
            )}
            {result.ui_elements && result.ui_elements.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">UI Elements ({result.ui_elements.length})</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {result.ui_elements.map((elem: any, i: number) => (
                    <div key={i} className="p-2 bg-muted/30 rounded text-sm text-foreground">
                      <span className="capitalize">{elem.element_type}</span>
                      <span className="text-muted-foreground ml-2">({(elem.confidence * 100).toFixed(0)}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {result.error_dialogs && result.error_dialogs.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-destructive mb-2">Error Dialogs Detected</h4>
                {result.error_dialogs.map((dialog: any, i: number) => (
                  <div key={i} className="p-3 bg-destructive/10 border border-destructive/20 rounded">
                    <p className="text-destructive text-sm">Error dialog detected at {(dialog.confidence * 100).toFixed(0)}% confidence</p>
                  </div>
                ))}
              </div>
            )}
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Description</h4>
              <p className="text-foreground">{result.description}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DocumentTab() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [performOCR, setPerformOCR] = useState(false)
  const [extractImages, setExtractImages] = useState(false)
  const [extractTables, setExtractTables] = useState(false)
  const processDocument = useProcessDocument()
  const [result, setResult] = useState<any>(null)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setResult(null)
  }

  const handleProcess = async () => {
    if (!selectedFile) return
    
    try {
      const response = await processDocument.mutateAsync({
        file: selectedFile,
        request: { perform_ocr, extract_images, extract_tables }
      })
      setResult(response)
    } catch (error) {
      console.error('Document processing failed:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
          className="hidden"
          id="document-upload"
        />
        <label htmlFor="document-upload" className="cursor-pointer">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-foreground font-medium">Upload PDF Document</p>
          <p className="text-sm text-muted-foreground mt-1">Click to browse or drag and drop</p>
        </label>
      </div>
      
      {selectedFile && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <span className="text-foreground">{selectedFile.name}</span>
          </div>
          
          <div className="space-y-3">
            <label className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50">
              <input
                type="checkbox"
                checked={performOCR}
                onChange={(e) => setPerformOCR(e.target.checked)}
                className="rounded"
              />
              <span className="text-foreground">Perform OCR on document</span>
            </label>
            <label className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50">
              <input
                type="checkbox"
                checked={extractImages}
                onChange={(e) => setExtractImages(e.target.checked)}
                className="rounded"
              />
              <span className="text-foreground">Extract images</span>
            </label>
            <label className="flex items-center gap-2 p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50">
              <input
                type="checkbox"
                checked={extractTables}
                onChange={(e) => setExtractTables(e.target.checked)}
                className="rounded"
              />
              <span className="text-foreground">Extract tables</span>
            </label>
          </div>
          
          <button
            onClick={handleProcess}
            disabled={processDocument.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {processDocument.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Scan className="h-4 w-4" />
            )}
            Process Document
          </button>
        </div>
      )}
      
      {result && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Document Processing Results</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground">Status</h4>
                <p className="text-foreground flex items-center gap-2">
                  {result.status === 'completed' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                  {result.status}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-muted-foreground">Pages</h4>
                <p className="text-foreground">{result.page_count}</p>
              </div>
            </div>
            {result.tables && result.tables.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Tables Extracted ({result.tables.length})</h4>
                <div className="space-y-2">
                  {result.tables.map((table: any, i: number) => (
                    <div key={i} className="p-3 bg-muted/30 rounded">
                      <p className="text-sm text-foreground">Page {table.page_number} - {table.rows} rows</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {result.images && result.images.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Images Extracted ({result.images.length})</h4>
                <p className="text-sm text-foreground">{result.images.length} images found in document</p>
              </div>
            )}
          </div>
        </div>
      )}
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
          No vision analysis history yet
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div key={item.uuid} className="p-4 bg-card border border-border rounded-lg">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium text-foreground capitalize">{item.analysis_type.replace('_', ' ')}</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
                <div className={`flex items-center gap-1 text-sm ${
                  item.status === 'completed' ? 'text-green-500' : 'text-red-500'
                }`}>
                  {item.status === 'completed' ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <XCircle className="h-4 w-4" />
                  )}
                  {item.status}
                </div>
              </div>
              {item.caption && (
                <p className="mt-2 text-sm text-foreground line-clamp-2">{item.caption}</p>
              )}
              {item.overall_confidence && (
                <div className="mt-2">
                  <ConfidenceScores overall={item.overall_confidence} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Sub-components
function ImageUpload({ onFileSelect }: { onFileSelect: (file: File) => void }) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0])
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0])
    }
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors"
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        id="image-upload"
      />
      <label htmlFor="image-upload" className="cursor-pointer">
        <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-foreground font-medium">Upload Image</p>
        <p className="text-sm text-muted-foreground mt-1">PNG, JPG, GIF, WebP up to 10MB</p>
      </label>
    </div>
  )
}

function ScreenshotUpload({ onFileSelect }: { onFileSelect: (file: File) => void }) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0])
    }
  }

  return (
    <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        id="screenshot-upload"
      />
      <label htmlFor="screenshot-upload" className="cursor-pointer">
        <Camera className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-foreground font-medium">Upload Screenshot</p>
        <p className="text-sm text-muted-foreground mt-1">PNG, JPG, GIF, WebP</p>
      </label>
    </div>
  )
}

function OCRViewer({ result }: { result: any }) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">OCR Results</h3>
        <ConfidenceScores overall={result.confidence} />
      </div>
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Extracted Text</h4>
          <div className="p-4 bg-muted/30 rounded-lg max-h-64 overflow-y-auto">
            <p className="text-foreground whitespace-pre-wrap">{result.text}</p>
          </div>
        </div>
        {result.language && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground">Detected Language</h4>
            <p className="text-foreground capitalize">{result.language}</p>
          </div>
        )}
        {result.blocks && result.blocks.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-2">Text Blocks ({result.blocks.length})</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {result.blocks.map((block: any, i: number) => (
                <div key={i} className="p-2 bg-muted/30 rounded text-sm">
                  <p className="text-foreground">{block.text}</p>
                  <p className="text-muted-foreground text-xs mt-1">Confidence: {(block.confidence * 100).toFixed(1)}%</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function BoundingBoxOverlay({ objects }: { objects: any[] }) {
  return (
    <div className="space-y-2">
      {objects.map((obj, i) => (
        <div key={i} className="flex items-center justify-between p-2 bg-muted/30 rounded">
          <span className="text-sm text-foreground capitalize">{obj.bounding_box.label}</span>
          <span className="text-sm text-muted-foreground">{(obj.bounding_box.confidence * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  )
}

function ConfidenceScores({ overall, processingTime }: { overall?: number; processingTime?: number }) {
  return (
    <div className="flex items-center gap-4 text-sm">
      {overall !== undefined && (
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Confidence:</span>
          <span className={`font-medium ${overall > 0.7 ? 'text-green-500' : overall > 0.4 ? 'text-yellow-500' : 'text-red-500'}`}>
            {(overall * 100).toFixed(0)}%
          </span>
        </div>
      )}
      {processingTime && (
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Time:</span>
          <span className="text-foreground">{processingTime.toFixed(2)}s</span>
        </div>
      )}
    </div>
  )
}
