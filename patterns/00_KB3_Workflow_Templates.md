# 00\_KB3\_Workflow\_Templates

# Workflow Templates with Data Transfer Integration

---

## title: "Workflow Templates and Patterns"

module: "00\_Framework" topics: \["workflow templates", "n8n patterns", "data transfer", "compression", "unlimited data", "best practices"\] contexts: \["workflow design", "template library", "implementation patterns", "performance optimization"\] difficulty: "intermediate" related\_sections: \["00\_KB3\_ImplementationGuide", "01\_Core\_DataTransfer", "02\_N8N\_WorkflowRegistry", "03\_Agents\_Catalog", "00\_KB3\_Agent\_Registry", "00\_KB3\_Templates"\]

## Core Approach

This module provides comprehensive workflow templates optimized for the KnowledgeForge 3.1 data transfer system. Each template includes intelligent compression, multi-part data handling, error recovery, and performance monitoring. These templates serve as starting points for building production-ready workflows that can handle unlimited data volumes efficiently. All templates follow patterns documented in `02_N8N_WorkflowRegistry.md` and deployment procedures from `00_KB3_ImplementationGuide.md`.

## Template Categories

### 1\. Data Transfer Foundation Templates

Essential templates that handle core data transfer functionality documented in `01_Core_DataTransfer.md`.

#### Master Data Transfer Handler Template

```json
{
  "name": "KF3.1 Master Data Transfer Handler",
  "meta": {
    "description": "Universal data transfer handler with compression and chunking support",
    "version": "3.1.0",
    "category": "foundation",
    "data_volume": "unlimited",
    "compression": "auto",
    "documentation": "01_Core_DataTransfer.md",
    "deployment_guide": "00_KB3_ImplementationGuide.md"
  },
  "nodes": [
    {
      "parameters": {
        "path": "data-transfer",
        "options": {
          "rawBody": true,
          "allowedMethods": ["GET", "POST"]
        }
      },
      "id": "webhook-entry",
      "name": "Data Transfer Entry Point",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300],
      "notes": "Accepts both chunked (GET) and direct (POST) data transfers per 01_Core_DataTransfer.md"
    },
    {
      "parameters": {
        "functionCode": "// KF3.1 Master Data Transfer Handler\n// Handles all data transfer patterns with intelligent routing\n// Implementation follows 01_Core_DataTransfer.md patterns\n\nconst sessionStorage = $workflow.sessionStorage || {};\nconst isChunkedTransfer = $json.query && ($json.query.chunk_index !== undefined || $json.query.action === 'complete');\nconst isDirectTransfer = $json.body && !isChunkedTransfer;\n\n// Load compression libraries safely (per 01_Core_DataTransfer.md)\nlet pako, LZString;\ntry {\n  pako = require('pako');\n  LZString = require('lz-string');\n} catch (error) {\n  console.warn('Compression libraries not fully available:', error.message);\n}\n\n// Universal decompression function (from 01_Core_DataTransfer.md)\nfunction decompressData(data, method) {\n  try {\n    switch (method) {\n      case 'pako':\n        if (!pako) throw new Error('Pako not available');\n        const compressed = Uint8Array.from(atob(data), c => c.charCodeAt(0));\n        return pako.inflate(compressed, { to: 'string' });\n        \n      case 'lz-string':\n        if (!LZString) throw new Error('LZ-String not available');\n        return LZString.decompressFromBase64(data);\n        \n      case 'native':\n        // Native decompression would require additional setup\n        throw new Error('Native decompression not supported in this environment');\n        \n      case 'none':\n      default:\n        return data;\n    }\n  } catch (error) {\n    console.error(`Decompression failed for method ${method}:`, error.message);\n    return data; // Return uncompressed data as fallback\n  }\n}\n\n// Session cleanup function (session management per 01_Core_DataTransfer.md)\nfunction cleanupExpiredSessions() {\n  const now = Date.now();\n  const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes\n  let cleanedCount = 0;\n  \n  Object.keys(sessionStorage).forEach(sessionId => {\n    const session = sessionStorage[sessionId];\n    if (now - new Date(session.created_at).getTime() > SESSION_TIMEOUT) {\n      delete sessionStorage[sessionId];\n      cleanedCount++;\n    }\n  });\n  \n  if (cleanedCount > 0) {\n    console.log(`Cleaned up ${cleanedCount} expired sessions`);\n  }\n}\n\n// Handle direct transfer (single request)\nif (isDirectTransfer) {\n  const requestData = typeof $json.body === 'string' ? JSON.parse($json.body) : $json.body;\n  const compressionMethod = requestData.compression_method || 'none';\n  \n  let processedData;\n  if (requestData.compressed_data) {\n    processedData = decompressData(requestData.compressed_data, compressionMethod);\n  } else {\n    processedData = requestData.data;\n  }\n  \n  return [{\n    json: {\n      success: true,\n      transfer_type: 'direct',\n      data: processedData,\n      compression_method: compressionMethod,\n      processing_time: Date.now() - requestData.timestamp,\n      documentation_ref: '01_Core_DataTransfer.md'\n    }\n  }];\n}\n\n// Handle chunked transfer (multi-part)\nif (isChunkedTransfer) {\n  const query = $json.query;\n  const sessionId = query.session_id;\n  const chunkIndex = parseInt(query.chunk_index);\n  const totalChunks = parseInt(query.total_chunks);\n  const action = query.action;\n  \n  // Initialize session if needed\n  if (!sessionStorage[sessionId] && action !== 'complete') {\n    sessionStorage[sessionId] = {\n      chunks: {},\n      created_at: new Date().toISOString(),\n      compression_method: query.compression_method || 'none',\n      expected_chunks: totalChunks\n    };\n  }\n  \n  const session = sessionStorage[sessionId];\n  \n  if (!session) {\n    return [{\n      json: {\n        success: false,\n        error: 'Session not found or expired',\n        session_id: sessionId,\n        troubleshooting: '01_Core_DataTransfer.md - Session Management'\n      }\n    }];\n  }\n  \n  // Store chunk data\n  if (action !== 'complete' && query.chunk_data) {\n    session.chunks[chunkIndex] = query.chunk_data;\n  }\n  \n  // Process complete transfer\n  if (action === 'complete' || Object.keys(session.chunks).length === session.expected_chunks) {\n    try {\n      // Reassemble chunks in order\n      let combinedData = '';\n      for (let i = 0; i < session.expected_chunks; i++) {\n        if (session.chunks[i]) {\n          combinedData += session.chunks[i];\n        }\n      }\n      \n      // Decompress if needed\n      const finalData = decompressData(combinedData, session.compression_method);\n      \n      // Clean up session\n      delete sessionStorage[sessionId];\n      \n      return [{\n        json: {\n          success: true,\n          transfer_type: 'chunked',\n          session_id: sessionId,\n          data: finalData,\n          compression_method: session.compression_method,\n          chunks_processed: session.expected_chunks,\n          documentation_ref: '01_Core_DataTransfer.md'\n        }\n      }];\n      \n    } catch (error) {\n      delete sessionStorage[sessionId];\n      return [{\n        json: {\n          success: false,\n          error: 'Failed to process chunked transfer',\n          details: error.message,\n          troubleshooting: '01_Core_DataTransfer.md - Error Handling'\n        }\n      }];\n    }\n  }\n  \n  // Acknowledge chunk receipt\n  return [{\n    json: {\n      success: true,\n      action: 'chunk_received',\n      session_id: sessionId,\n      chunk_index: chunkIndex,\n      chunks_received: Object.keys(session.chunks).length,\n      chunks_expected: session.expected_chunks\n    }\n  }];\n}\n\n// Cleanup expired sessions\ncleanupExpiredSessions();\n\n// Default response for health checks\nreturn [{\n  json: {\n    success: true,\n    status: 'data_transfer_handler_ready',\n    version: '3.1.0',\n    capabilities: ['direct_transfer', 'chunked_transfer', 'compression_support'],\n    compression_methods: ['pako', 'lz-string', 'native', 'none'],\n    documentation: '01_Core_DataTransfer.md'\n  }\n}];"
      },
      "id": "data-processor",
      "name": "Data Transfer Processor",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [440, 300]
    }
  ],
  "connections": {
    "Data Transfer Entry Point": {
      "main": [["Data Transfer Processor"]]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "saveDataSuccessExecution": "all",
    "saveDataErrorExecution": "all"
  }
}
```

### 2\. Agent Integration Templates

Templates for integrating with AI agents from `03_Agents_Catalog.md`.

#### Agent Router Template

```json
{
  "name": "KF3.1 Agent Router with Data Transfer",
  "meta": {
    "description": "Routes requests to appropriate agents with data transfer support",
    "version": "3.1.0",
    "category": "agent_integration",
    "agent_registry": "03_Agents_Catalog.md",
    "data_transfer": "01_Core_DataTransfer.md"
  },
  "nodes": [
    {
      "parameters": {
        "path": "agents/route",
        "options": {
          "allowedMethods": ["GET", "POST"]
        }
      },
      "id": "agent-webhook",
      "name": "Agent Router Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "functionCode": "// KF3.1 Agent Router with Data Transfer Support\n// Routes requests to appropriate agents from 03_Agents_Catalog.md\n// Supports unlimited data transfer per 01_Core_DataTransfer.md\n\nconst requestData = $json.query || $json.body || $json;\nconst agentType = requestData.agent_type || 'navigator';\nconst query = requestData.query || requestData.payload || '';\nconst context = requestData.context || {};\nconst sessionId = requestData.session_id;\n\n// Agent registry (configurations from 03_Agents_Catalog.md)\nconst agentRegistry = {\n  navigator: {\n    id: 'navigator-agent-001',\n    name: 'KnowledgeForge Navigator',\n    endpoint: process.env.NAVIGATOR_AGENT_URL,\n    capabilities: ['knowledge_discovery', 'decision_tree_navigation', 'user_guidance'],\n    max_data_size: 'unlimited',\n    compression_support: ['pako', 'lz-string', 'native'],\n    catalog_reference: '03_Agents_Catalog.md - Navigator Agent'\n  },\n  expert: {\n    id: 'expert-agent-001',\n    name: 'Domain Expert Agent',\n    endpoint: process.env.EXPERT_AGENT_URL,\n    capabilities: ['deep_analysis', 'domain_expertise', 'complex_reasoning'],\n    max_data_size: 'unlimited',\n    compression_support: ['pako', 'lz-string'],\n    catalog_reference: '03_Agents_Catalog.md - Expert Agent'\n  },\n  utility: {\n    id: 'utility-agent-001',\n    name: 'Utility Agent',\n    endpoint: process.env.UTILITY_AGENT_URL,\n    capabilities: ['quick_tasks', 'data_processing', 'format_conversion'],\n    max_data_size: '50MB',\n    compression_support: ['lz-string', 'none'],\n    catalog_reference: '03_Agents_Catalog.md - Utility Agent'\n  }\n};\n\n// Select agent based on type and data requirements\nconst selectedAgent = agentRegistry[agentType];\nif (!selectedAgent) {\n  return [{\n    json: {\n      success: false,\n      error: 'Unknown agent type',\n      available_agents: Object.keys(agentRegistry),\n      agent_catalog: '03_Agents_Catalog.md'\n    }\n  }];\n}\n\n// Prepare agent request with data transfer considerations\nconst dataSize = JSON.stringify(requestData).length;\nlet compressionRecommended = false;\nlet recommendedMethod = 'none';\n\nif (dataSize > 10000) { // > 10KB\n  compressionRecommended = true;\n  // Select compression method based on agent support and data characteristics\n  if (selectedAgent.compression_support.includes('pako') && dataSize > 100000) {\n    recommendedMethod = 'pako'; // Best compression for large data\n  } else if (selectedAgent.compression_support.includes('lz-string')) {\n    recommendedMethod = 'lz-string'; // Fast compression\n  }\n}\n\n// Prepare agent request payload\nconst agentRequest = {\n  agent_info: {\n    id: selectedAgent.id,\n    name: selectedAgent.name,\n    type: agentType,\n    catalog_reference: selectedAgent.catalog_reference\n  },\n  request: {\n    query: query,\n    context: context,\n    session_id: sessionId,\n    timestamp: new Date().toISOString()\n  },\n  data_transfer: {\n    original_size: dataSize,\n    compression_recommended: compressionRecommended,\n    recommended_method: recommendedMethod,\n    agent_max_size: selectedAgent.max_data_size,\n    reference: '01_Core_DataTransfer.md'\n  },\n  routing_info: {\n    endpoint: selectedAgent.endpoint,\n    timeout: 300000, // 5 minutes default\n    retry_policy: 'exponential_backoff',\n    max_retries: 3\n  }\n};\n\nconsole.log(`Routing to ${selectedAgent.name} (${agentType})`);\nconsole.log(`Data size: ${dataSize} bytes, compression: ${compressionRecommended ? recommendedMethod : 'none'}`);\n\nreturn [{\n  json: {\n    success: true,\n    routed_to: selectedAgent.name,\n    agent_type: agentType,\n    agent_request: agentRequest,\n    performance_info: {\n      data_size: dataSize,\n      compression_recommended: compressionRecommended,\n      estimated_processing_time: Math.max(5000, dataSize / 1000) // Rough estimate\n    },\n    documentation_references: {\n      agent_catalog: '03_Agents_Catalog.md',\n      data_transfer: '01_Core_DataTransfer.md',\n      implementation: '00_KB3_ImplementationGuide.md'\n    }\n  }\n}];"
      },
      "id": "route-processor",
      "name": "Agent Route Processor",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [440, 300]
    }
  ],
  "connections": {
    "Agent Router Webhook": {
      "main": [["Agent Route Processor"]]
    }
  }
}
```

### 3\. Application-Specific Templates

Templates for common use cases with full data transfer integration.

#### Content Analysis Pipeline Template

```json
{
  "name": "KF3.1 Content Analysis Pipeline",
  "meta": {
    "description": "Processes large volumes of content with AI analysis",
    "category": "content_processing",
    "data_volume": "1MB - 100MB",
    "compression": "lz-string optimized",
    "agent_integration": "03_Agents_Catalog.md - Content Analysis Agent",
    "data_transfer": "01_Core_DataTransfer.md"
  },
  "nodes": [
    {
      "parameters": {
        "path": "content-analysis",
        "options": {
          "allowedMethods": ["GET", "POST"]
        }
      },
      "id": "content-webhook",
      "name": "Content Analysis Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "functionCode": "// KF3.1 Content Analysis Data Processor\n// Optimized for text-heavy content with LZ-String compression\n// Follows patterns from 01_Core_DataTransfer.md\n\nconst data = $json.processed_data || $json.data;\nconst transferMetrics = $json.transfer_metrics || {};\nconst metadata = $json.processing_metadata || $json.metadata || {};\n\n// Validate content data structure\nif (!data || (!data.content_items && !data.articles && !data.posts)) {\n  return [{\n    json: {\n      error: 'Invalid content data structure',\n      expected: 'content_items, articles, or posts array',\n      received: Object.keys(data || {}),\n      troubleshooting: '00_KB3_ImplementationGuide.md - Data Validation'\n    }\n  }];\n}\n\n// Normalize content structure\nconst contentItems = data.content_items || data.articles || data.posts || [];\nconst contentCount = Array.isArray(contentItems) ? contentItems.length : 0;\n\n// Determine processing strategy based on volume (per 01_Core_DataTransfer.md)\nlet processingStrategy;\nif (contentCount < 100) {\n  processingStrategy = 'immediate_processing';\n} else if (contentCount < 1000) {\n  processingStrategy = 'batch_processing';\n} else {\n  processingStrategy = 'chunked_processing';\n}\n\n// Content analysis configuration\nconst analysisConfig = {\n  sentiment_analysis: metadata.include_sentiment !== false,\n  topic_extraction: metadata.include_topics !== false,\n  entity_recognition: metadata.include_entities !== false,\n  language_detection: metadata.include_language !== false,\n  quality_scoring: metadata.include_quality !== false,\n  readability_analysis: metadata.include_readability !== false,\n  \n  // Performance optimizations (from 01_Core_DataTransfer.md)\n  parallel_processing: processingStrategy !== 'immediate_processing',\n  batch_size: processingStrategy === 'chunked_processing' ? 50 : contentCount,\n  cache_results: contentCount > 500,\n  \n  // Output configuration\n  output_format: metadata.output_format || 'detailed',\n  include_raw_scores: metadata.include_raw_scores || false,\n  aggregate_statistics: metadata.aggregate_statistics !== false\n};\n\n// Prepare for Claude Project processing (integration per 03_Agents_Catalog.md)\nconst claudePayload = {\n  operation: 'comprehensive_content_analysis',\n  content_data: {\n    items: contentItems,\n    total_count: contentCount,\n    data_source: metadata.source || 'unknown',\n    collection_timestamp: metadata.timestamp || new Date().toISOString()\n  },\n  analysis_configuration: analysisConfig,\n  processing_context: {\n    strategy: processingStrategy,\n    expected_duration: this.estimateProcessingTime(contentCount, analysisConfig),\n    memory_requirements: this.estimateMemoryRequirements(contentCount),\n    optimization_target: metadata.optimization_target || 'balanced'\n  },\n  transfer_info: transferMetrics,\n  quality_requirements: {\n    min_confidence: metadata.min_confidence || 0.7,\n    max_processing_time: metadata.max_processing_time || 1800000, // 30 minutes\n    required_accuracy: metadata.required_accuracy || 0.85\n  },\n  documentation_references: {\n    data_transfer: '01_Core_DataTransfer.md',\n    agent_catalog: '03_Agents_Catalog.md - Content Analysis Agent',\n    implementation: '00_KB3_ImplementationGuide.md'\n  }\n};\n\nconsole.log(`Content Analysis: ${contentCount} items, strategy: ${processingStrategy}`);\nconsole.log(`Transfer metrics:`, {\n  size: transferMetrics.final_data_size || transferMetrics.data_size,\n  compression: transferMetrics.compression_ratio || 'none',\n  chunks: transferMetrics.chunks_processed || transferMetrics.chunks || 1\n});\n\nreturn [{ json: claudePayload }];\n\n// Helper functions\nthis.estimateProcessingTime = function(itemCount, config) {\n  let baseTimePerItem = 2000; // 2 seconds per item\n  \n  // Adjust based on analysis complexity\n  const complexityFactors = [\n    config.sentiment_analysis ? 1.2 : 1,\n    config.topic_extraction ? 1.3 : 1,\n    config.entity_recognition ? 1.4 : 1,\n    config.language_detection ? 1.1 : 1,\n    config.quality_scoring ? 1.2 : 1,\n    config.readability_analysis ? 1.1 : 1\n  ];\n  \n  const complexityMultiplier = complexityFactors.reduce((a, b) => a * b, 1);\n  const parallelismFactor = config.parallel_processing ? 0.4 : 1;\n  \n  return Math.ceil(itemCount * baseTimePerItem * complexityMultiplier * parallelismFactor);\n};\n\nthis.estimateMemoryRequirements = function(itemCount) {\n  // Rough memory estimation in MB\n  const baseMemoryPerItem = 0.1; // 100KB per item\n  const bufferFactor = 1.5; // 50% buffer\n  \n  return Math.ceil(itemCount * baseMemoryPerItem * bufferFactor);\n};"
      },
      "id": "content-processor",
      "name": "Content Data Processor",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [440, 300]
    }
  ],
  "connections": {
    "Content Analysis Webhook": {
      "main": [["Content Data Processor"]]
    }
  }
}
```

### 4\. Data Analytics Templates

Templates for processing large analytical datasets.

#### Analytics Data Pipeline Template

```json
{
  "name": "KF3.1 Analytics Data Pipeline",
  "meta": {
    "description": "Processes large analytical datasets with performance optimization",
    "category": "data_analytics",
    "data_volume": "10MB - 1GB",
    "compression": "pako optimized",
    "agent_integration": "03_Agents_Catalog.md - Data Analytics Agent",
    "performance_reference": "01_Core_DataTransfer.md - Performance Optimization"
  },
  "nodes": [
    {
      "parameters": {
        "path": "analytics-pipeline",
        "options": {
          "allowedMethods": ["GET", "POST"],
          "rawBody": true
        }
      },
      "id": "analytics-webhook",
      "name": "Analytics Pipeline Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "functionCode": "// KF3.1 Analytics Data Pipeline\n// Optimized for large structured datasets with Pako compression\n// Performance patterns from 01_Core_DataTransfer.md\n\nconst requestData = $json;\nconst analyticsData = requestData.analytics_data || requestData.data;\nconst transferMetrics = requestData.transfer_metrics || {};\nconst processingOptions = requestData.processing_options || {};\n\n// Validate analytics data structure\nif (!analyticsData || !Array.isArray(analyticsData.records)) {\n  return [{\n    json: {\n      success: false,\n      error: 'Invalid analytics data structure',\n      expected: 'analytics_data.records array required',\n      received_structure: Object.keys(analyticsData || {}),\n      troubleshooting: '00_KB3_ImplementationGuide.md - Data Validation'\n    }\n  }];\n}\n\nconst records = analyticsData.records;\nconst recordCount = records.length;\nconst dataStructure = this.analyzeDataStructure(analyticsData);\n\n// Determine processing strategy based on data volume and complexity\nlet processingStrategy;\nlet compressionRecommendation;\n\nif (recordCount < 1000 && dataStructure.estimatedSize < 1000000) { // < 1MB\n  processingStrategy = 'in_memory_processing';\n  compressionRecommendation = 'lz-string';\n} else if (recordCount < 50000 && dataStructure.estimatedSize < 50000000) { // < 50MB\n  processingStrategy = 'batch_processing';\n  compressionRecommendation = 'pako';\n} else {\n  processingStrategy = 'streaming_processing';\n  compressionRecommendation = 'pako';\n}\n\n// Configure analytics processing\nconst analyticsConfig = {\n  // Data processing options\n  aggregation_functions: processingOptions.aggregations || ['sum', 'avg', 'count'],\n  grouping_columns: processingOptions.group_by || [],\n  filter_conditions: processingOptions.filters || [],\n  sort_order: processingOptions.sort || [],\n  \n  // Performance optimizations (per 01_Core_DataTransfer.md)\n  processing_strategy: processingStrategy,\n  compression_method: compressionRecommendation,\n  chunk_size: processingStrategy === 'streaming_processing' ? 1000 : recordCount,\n  parallel_processing: recordCount > 5000,\n  cache_intermediate_results: recordCount > 10000,\n  \n  // Output configuration\n  output_format: processingOptions.output_format || 'detailed',\n  include_metadata: processingOptions.include_metadata !== false,\n  generate_summary: processingOptions.generate_summary !== false,\n  \n  // Quality and validation\n  data_quality_check: processingOptions.quality_check !== false,\n  outlier_detection: processingOptions.detect_outliers || false,\n  null_value_handling: processingOptions.null_handling || 'exclude'\n};\n\n// Prepare for analytics agent processing (per 03_Agents_Catalog.md)\nconst analyticsPayload = {\n  operation: 'comprehensive_data_analytics',\n  dataset: {\n    records: records,\n    metadata: analyticsData.metadata || {},\n    structure: dataStructure,\n    record_count: recordCount,\n    data_source: analyticsData.source || 'unknown',\n    collection_timestamp: analyticsData.timestamp || new Date().toISOString()\n  },\n  processing_configuration: analyticsConfig,\n  performance_context: {\n    strategy: processingStrategy,\n    estimated_duration: this.estimateProcessingTime(recordCount, dataStructure, analyticsConfig),\n    memory_requirements: this.estimateMemoryRequirements(recordCount, dataStructure),\n    compression_recommendation: compressionRecommendation,\n    optimization_target: processingOptions.optimization_target || 'balanced'\n  },\n  transfer_metrics: transferMetrics,\n  quality_requirements: {\n    accuracy_threshold: processingOptions.accuracy_threshold || 0.95,\n    max_processing_time: processingOptions.max_processing_time || 3600000, // 1 hour\n    memory_limit: processingOptions.memory_limit || '2GB'\n  },\n  documentation_references: {\n    data_transfer: '01_Core_DataTransfer.md - Analytics Optimization',\n    agent_catalog: '03_Agents_Catalog.md - Data Analytics Agent',\n    implementation: '00_KB3_ImplementationGuide.md - Analytics Setup'\n  }\n};\n\nconsole.log(`Analytics Pipeline: ${recordCount} records, strategy: ${processingStrategy}`);\nconsole.log(`Data structure:`, {\n  columns: dataStructure.columnCount,\n  estimated_size: `${(dataStructure.estimatedSize / 1024 / 1024).toFixed(2)}MB`,\n  compression: compressionRecommendation\n});\n\nreturn [{ json: analyticsPayload }];\n\n// Helper functions for analytics processing\nthis.analyzeDataStructure = function(analyticsData) {\n  const records = analyticsData.records || [];\n  if (records.length === 0) {\n    return {\n      columnCount: 0,\n      dataTypes: {},\n      estimatedSize: 0,\n      recordCount: 0\n    };\n  }\n  \n  const sampleRecord = records[0];\n  const columns = Object.keys(sampleRecord);\n  const dataTypes = {};\n  \n  // Analyze data types\n  columns.forEach(column => {\n    const value = sampleRecord[column];\n    if (typeof value === 'number') {\n      dataTypes[column] = 'number';\n    } else if (typeof value === 'boolean') {\n      dataTypes[column] = 'boolean';\n    } else if (value instanceof Date || /\\d{4}-\\d{2}-\\d{2}/.test(value)) {\n      dataTypes[column] = 'date';\n    } else {\n      dataTypes[column] = 'string';\n    }\n  });\n  \n  // Estimate data size\n  const avgRecordSize = JSON.stringify(sampleRecord).length;\n  const estimatedSize = avgRecordSize * records.length;\n  \n  return {\n    columnCount: columns.length,\n    columns: columns,\n    dataTypes: dataTypes,\n    estimatedSize: estimatedSize,\n    recordCount: records.length\n  };\n};\n\nthis.estimateProcessingTime = function(recordCount, structure, config) {\n  // Base processing time: 0.1ms per record\n  let baseTime = recordCount * 0.1;\n  \n  // Adjust for data complexity\n  const complexityMultiplier = 1 + (structure.columnCount * 0.1);\n  \n  // Adjust for operations\n  const operationMultipliers = {\n    aggregation: config.aggregation_functions.length * 1.5,\n    grouping: config.grouping_columns.length * 2,\n    filtering: config.filter_conditions.length * 1.2,\n    sorting: config.sort_order.length * 1.8\n  };\n  \n  const totalMultiplier = Object.values(operationMultipliers).reduce((a, b) => a + b, 0) || 1;\n  \n  // Apply parallelism reduction\n  const parallelismFactor = config.parallel_processing ? 0.3 : 1;\n  \n  return Math.ceil(baseTime * complexityMultiplier * totalMultiplier * parallelismFactor);\n};\n\nthis.estimateMemoryRequirements = function(recordCount, structure) {\n  // Base memory: 50 bytes per field\n  const baseMemoryPerRecord = structure.columnCount * 50;\n  const totalBaseMemory = recordCount * baseMemoryPerRecord;\n  \n  // Add overhead for processing (sorting, grouping, etc.)\n  const processingOverhead = totalBaseMemory * 0.5;\n  \n  // Convert to MB and add buffer\n  const totalMemoryMB = (totalBaseMemory + processingOverhead) / 1024 / 1024;\n  \n  return Math.ceil(totalMemoryMB * 1.2); // 20% buffer\n};"
      },
      "id": "analytics-processor",
      "name": "Analytics Data Processor",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [440, 300]
    }
  ],
  "connections": {
    "Analytics Pipeline Webhook": {
      "main": [["Analytics Data Processor"]]
    }
  }
}
```

## Template Optimization Patterns

### 1\. Performance Optimization

```javascript
// Template performance optimization patterns (from 01_Core_DataTransfer.md)
const optimizationPatterns = {
    compression_selection: {
        text_heavy: 'lz-string',     // Fast, good for text
        structured_data: 'pako',     // Best compression for JSON
        mixed_content: 'auto',       // Let system decide
        real_time: 'lz-string',      // Fastest processing
        batch_processing: 'pako'     // Maximum compression
    },
    
    chunking_strategy: {
        small_data: 2000,            // < 1MB
        medium_data: 4000,           // 1-10MB
        large_data: 8000,            // > 10MB
        network_optimized: 6000      // Balanced approach
    },
    
    timeout_configuration: {
        real_time: 30000,            // 30 seconds
        standard: 300000,            // 5 minutes
        batch_processing: 1800000,   // 30 minutes
        large_data: 3600000          // 1 hour
    },
    
    documentation_references: {
        data_transfer: '01_Core_DataTransfer.md',
        implementation: '00_KB3_ImplementationGuide.md',
        agents: '03_Agents_Catalog.md',
        workflows: '02_N8N_WorkflowRegistry.md'
    }
};
```

### 2\. Error Handling Standards

```javascript
// Standardized error handling for templates (per 00_KB3_ImplementationGuide.md)
const errorHandlingPatterns = {
    categorizeError: (error) => {
        if (error.includes('session')) return 'session_management';
        if (error.includes('compression')) return 'compression_error';
        if (error.includes('timeout')) return 'timeout_error';
        if (error.includes('validation')) return 'data_validation';
        return 'unknown_error';
    },
    
    generateErrorResponse: (errorType, originalError) => ({
        success: false,
        error: {
            category: errorType,
            message: originalError,
            retryable: ['session_management', 'timeout_error'].includes(errorType),
            timestamp: new Date().toISOString(),
            troubleshooting_guide: '00_KB3_ImplementationGuide.md - Troubleshooting',
            data_transfer_guide: '01_Core_DataTransfer.md - Error Recovery'
        }
    }),
    
    recovery_strategies: {
        session_management: 'restart_session',
        compression_error: 'fallback_compression',
        timeout_error: 'retry_with_smaller_chunks',
        data_validation: 'validate_and_transform'
    }
};
```

### 3\. Monitoring Integration

```javascript
// Standard monitoring integration for templates (per 00_KB3_ImplementationGuide.md)
const monitoringIntegration = {
    logTransferMetrics: (metrics) => {
        console.log('Transfer Metrics:', {
            size: metrics.data_size,
            compression: metrics.compression_ratio,
            duration: metrics.processing_time_ms,
            chunks: metrics.chunks_processed,
            agent_ref: metrics.agent_catalog_ref || '03_Agents_Catalog.md'
        });
    },
    
    trackPerformance: (startTime, endTime, dataSize) => {
        const duration = endTime - startTime;
        const throughput = (dataSize / 1024 / 1024) / (duration / 1000);
        
        return {
            duration_ms: duration,
            throughput_mbps: throughput.toFixed(3),
            efficiency_score: throughput > 1 ? 'excellent' : throughput > 0.5 ? 'good' : 'needs_optimization',
            optimization_reference: '01_Core_DataTransfer.md - Performance Optimization'
        };
    },
    
    generatePerformanceReport: (templateName, metrics) => {
        return {
            template: templateName,
            timestamp: new Date().toISOString(),
            performance_metrics: metrics,
            recommendations: generateOptimizationRecommendations(metrics),
            documentation_references: {
                performance_guide: '01_Core_DataTransfer.md - Performance Optimization',
                implementation_guide: '00_KB3_ImplementationGuide.md - Performance Monitoring',
                workflow_registry: '02_N8N_WorkflowRegistry.md'
            }
        };
    }
};
```

## Template Deployment Patterns

### Standard Deployment Process

1. **Template Selection** \- Choose appropriate template based on use case and data characteristics  
2. **Customization** \- Modify compression settings, processing logic, and agent integrations  
3. **Validation** \- Test with sample data using procedures from `00_KB3_ImplementationGuide.md`  
4. **Deployment** \- Deploy to N8N following patterns in `02_N8N_WorkflowRegistry.md`  
5. **Monitoring** \- Set up performance tracking per `00_KB3_ImplementationGuide.md`

### Integration Requirements

- **Data Transfer Setup** \- Implement compression libraries per `01_Core_DataTransfer.md`  
- **Agent Configuration** \- Connect to agents from `03_Agents_Catalog.md`  
- **Performance Monitoring** \- Enable tracking per `00_KB3_ImplementationGuide.md`  
- **Error Handling** \- Implement recovery strategies from troubleshooting guides

## Implementation Notes

- All templates follow standards defined in `00_KB3_Templates.md`  
- Data transfer capabilities leverage `01_Core_DataTransfer.md` for unlimited data processing  
- Agent integrations use configurations from `03_Agents_Catalog.md`  
- Deployment procedures follow `00_KB3_ImplementationGuide.md`  
- Performance optimization techniques documented in `01_Core_DataTransfer.md`  
- Error handling and troubleshooting guidance in `00_KB3_ImplementationGuide.md`

## Next Steps and Recommendations

1. **Choose appropriate templates** \- Select based on your use case and data characteristics  
2. **Customize for your needs** \- Modify compression settings and processing logic per `01_Core_DataTransfer.md`  
3. **Test with sample data** \- Validate performance with realistic datasets using `04_TestScenarios.md`  
4. **Deploy to production** \- Follow deployment procedures in `00_KB3_ImplementationGuide.md`  
5. **Create custom templates** \- Build specialized templates following `00_KB3_Templates.md` standards

## Next Steps

1️⃣ **Select template for your use case** → Review categories and choose appropriate template   
2️⃣ **Configure data transfer settings** → 01\_Core\_DataTransfer.md (Configuration Guide)   
3️⃣ **Deploy to N8N environment** → 00\_KB3\_ImplementationGuide.md (Workflow Deployment)   
4️⃣ **Test with sample data** → 04\_TestScenarios.md (Template Testing)   
5️⃣ **Monitor and optimize performance** → 00\_KB3\_ImplementationGuide.md (Performance Monitoring)

