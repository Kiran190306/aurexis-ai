# Jarvis AI - Database Schema Documentation

## Overview

This document describes the complete database schema for Jarvis AI, an enterprise-grade AI Agent Platform. The schema is designed to support all core modules including authentication, conversations, memory, tools, plugins, agents, prompts, documents, files, calendar, and notifications.

## Database Technology

- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (Async)
- **Migrations**: Alembic
- **Connection Pooling**: SQLAlchemy Pool

## Schema Design Principles

1. **Soft Deletes**: All major tables include `deleted_at` for soft deletion
2. **UUID**: All entities have both integer ID and UUID for external references
3. **Timestamps**: All tables include `created_at` and `updated_at`
4. **Timezone Awareness**: All datetime fields use timezone-aware timestamps
5. **Foreign Keys**: All foreign keys include ON DELETE CASCADE/SET NULL
6. **Indexes**: Strategic indexes on frequently queried columns
7. **JSON Fields**: Flexible metadata stored as JSON for extensibility

## Core Tables

### Users & Authentication

#### users
Stores user accounts and authentication information.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `email` (String, Unique): User email
- `username` (String, Unique): Unique username
- `full_name` (String): Full name
- `avatar_url` (String): Profile picture URL
- `bio` (Text): User biography
- `hashed_password` (String): Bcrypt hashed password
- `is_active` (Boolean): Account status
- `is_verified` (Boolean): Email verification status
- `is_superuser` (Boolean): Admin privileges
- `role` (Enum): user, admin, moderator, developer
- `oauth_provider` (Enum): google, github, microsoft
- `oauth_id` (String): OAuth provider ID
- `mfa_enabled` (Boolean): Multi-factor authentication
- `mfa_secret` (String): TOTP secret
- `last_login` (DateTime): Last login timestamp
- `failed_login_attempts` (Integer): Failed login count
- `locked_until` (DateTime): Account lock expiration
- `timezone` (String): User timezone
- `language` (String): User language preference
- `theme` (String): UI theme preference
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- UNIQUE on `email`
- UNIQUE on `username`
- INDEX on `oauth_id`

#### user_settings
Stores user-specific settings and preferences.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `default_model` (String): Default AI model
- `default_temperature` (Integer): Default temperature (0-100)
- `default_max_tokens` (Integer): Default max tokens
- `enable_streaming` (Boolean): Enable response streaming
- `memory_retention_days` (Integer): Memory retention period
- `enable_long_term_memory` (Boolean): Long-term memory enabled
- `enable_short_term_memory` (Boolean): Short-term memory enabled
- `enable_browse` (Boolean): Browser tool enabled
- `enable_terminal` (Boolean): Terminal tool enabled
- `enable_github` (Boolean): GitHub tool enabled
- `enable_voice` (Boolean): Voice features enabled
- `enable_image` (Boolean): Image features enabled
- `enable_document` (Boolean): Document features enabled
- `enable_calendar` (Boolean): Calendar features enabled
- `email_notifications` (Boolean): Email notifications enabled
- `push_notifications` (Boolean): Push notifications enabled
- `sms_notifications` (Boolean): SMS notifications enabled
- `notification_frequency` (String): Notification frequency
- `data_sharing_enabled` (Boolean): Data sharing consent
- `analytics_enabled` (Boolean): Analytics consent
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### api_keys
Stores API keys for programmatic access.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `key` (String, Unique): API key
- `name` (String): Key name
- `description` (Text): Key description
- `scopes` (JSON): Array of scopes
- `is_active` (Boolean): Key status
- `rate_limit_per_minute` (Integer): Rate limit per minute
- `rate_limit_per_hour` (Integer): Rate limit per hour
- `expires_at` (DateTime): Expiration timestamp
- `last_used` (DateTime): Last usage timestamp
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `key`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### sessions
Stores user sessions for authentication.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `token` (String, Unique): Session token
- `refresh_token` (String, Unique): Refresh token
- `device_type` (String): Device type (desktop, mobile, tablet)
- `device_name` (String): Device name
- `os` (String): Operating system
- `browser` (String): Browser name
- `ip_address` (String): IP address
- `user_agent` (Text): User agent string
- `is_active` (Boolean): Session status
- `expires_at` (DateTime): Expiration timestamp
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `token`
- UNIQUE on `refresh_token`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

### Conversations & Messages

#### conversations
Stores chat conversations.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `title` (String): Conversation title
- `description` (Text): Conversation description
- `status` (Enum): active, archived, deleted, pinned
- `model` (String): AI model used
- `temperature` (Integer): Temperature setting (0-100)
- `max_tokens` (Integer): Max tokens setting
- `system_prompt` (Text): System prompt
- `tags` (JSON): Array of tags
- `metadata` (JSON): Additional metadata
- `is_shared` (Boolean): Sharing enabled
- `share_token` (String, Unique): Share token
- `message_count` (Integer): Total message count
- `token_count` (Integer): Total token count
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp
- `last_message_at` (DateTime): Last message timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- UNIQUE on `share_token`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### messages
Stores individual messages within conversations.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `conversation_id` (Integer, FK): Reference to conversations
- `user_id` (Integer, FK): Reference to users
- `role` (Enum): user, assistant, system, tool
- `content` (Text): Message content
- `message_type` (Enum): text, code, image, file, system, tool_call, tool_response
- `code_language` (String): Code language (for code messages)
- `code_content` (Text): Code content (for code messages)
- `image_url` (String): Image URL (for image messages)
- `image_alt` (String): Image alt text
- `file_id` (Integer, FK): Reference to files
- `tool_calls` (JSON): Tool call data
- `tool_response` (JSON): Tool response data
- `metadata` (JSON): Additional metadata
- `parent_message_id` (Integer, FK): Reference to messages (for threading)
- `prompt_tokens` (Integer): Prompt token count
- `completion_tokens` (Integer): Completion token count
- `total_tokens` (Integer): Total token count
- `is_edited` (Boolean): Edit status
- `is_deleted` (Boolean): Deletion status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `conversation_id`
- INDEX on `user_id`
- FOREIGN KEY on `conversation_id` → `conversations.id` (CASCADE)
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `parent_message_id` → `messages.id` (SET NULL)

#### conversation_shares
Stores shared conversation links.

**Columns:**
- `id` (Integer, PK): Primary key
- `conversation_id` (Integer, FK): Reference to conversations
- `share_token` (String, Unique): Share token
- `shared_by` (Integer, FK): Reference to users
- `access_count` (Integer): Access count
- `max_accesses` (Integer): Maximum accesses
- `expires_at` (DateTime): Expiration timestamp
- `password_hash` (String): Password hash
- `is_active` (Boolean): Share status
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `share_token`
- FOREIGN KEY on `conversation_id` → `conversations.id` (CASCADE)
- FOREIGN KEY on `shared_by` → `users.id` (CASCADE)

### Memory System

#### memories
Stores long-term and short-term memories.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `content` (Text): Memory content
- `summary` (Text): Memory summary
- `memory_type` (Enum): episodic, semantic, procedural, declarative, working
- `embedding` (JSON): Vector embedding
- `embedding_model` (String): Embedding model used
- `tags` (JSON): Array of tags
- `entities` (JSON): Extracted entities
- `metadata` (JSON): Additional metadata
- `importance_score` (Float): Importance score (0-1)
- `access_count` (Integer): Access count
- `last_accessed` (DateTime): Last access timestamp
- `conversation_id` (Integer, FK): Reference to conversations
- `message_id` (Integer, FK): Reference to messages
- `status` (Enum): active, archived, deleted, consolidated
- `is_pinned` (Boolean): Pinned status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp
- `expires_at` (DateTime): Expiration timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `conversation_id` → `conversations.id` (SET NULL)
- FOREIGN KEY on `message_id` → `messages.id` (SET NULL)

#### memory_associations
Stores associations between memories.

**Columns:**
- `id` (Integer, PK): Primary key
- `memory_id_1` (Integer, FK): Reference to memories
- `memory_id_2` (Integer, FK): Reference to memories
- `association_type` (String): Association type
- `strength` (Float): Association strength (0-1)
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `memory_id_1` → `memories.id` (CASCADE)
- FOREIGN KEY on `memory_id_2` → `memories.id` (CASCADE)

#### memory_consolidations
Stores memory consolidation operations.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `source_memory_ids` (JSON): Array of source memory IDs
- `consolidated_memory_id` (Integer, FK): Reference to memories
- `consolidation_type` (String): Consolidation type
- `status` (String): Status (pending, processing, completed, failed)
- `result_summary` (Text): Result summary
- `error_message` (Text): Error message
- `created_at` (DateTime): Creation timestamp
- `completed_at` (DateTime): Completion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `consolidated_memory_id` → `memories.id` (SET NULL)

#### working_memory
Stores short-term working memory for conversations.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `conversation_id` (Integer, FK): Reference to conversations
- `context_data` (JSON): Current context
- `context_window` (JSON): Context window
- `current_task` (Text): Current task
- `current_goal` (Text): Current goal
- `intermediate_steps` (JSON): Intermediate steps
- `token_count` (Integer): Token count
- `max_tokens` (Integer): Max tokens
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `conversation_id` → `conversations.id` (CASCADE)

### Tool System

#### tools
Stores custom and built-in tools.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `name` (String, Unique): Tool name
- `display_name` (String): Display name
- `description` (Text): Tool description
- `version` (String): Tool version
- `tool_type` (Enum): built_in, custom, plugin
- `status` (Enum): active, inactive, deprecated, maintenance
- `config_schema` (JSON): Configuration schema
- `config` (JSON): Default configuration
- `parameters` (JSON): Parameters definition
- `execution_type` (String): Execution type (http, function, script)
- `endpoint` (String): HTTP endpoint
- `method` (String): HTTP method
- `headers` (JSON): HTTP headers
- `authentication` (JSON): Authentication config
- `code` (Text): Tool code
- `language` (String): Code language
- `plugin_id` (Integer, FK): Reference to plugins
- `required_permissions` (JSON): Required permissions
- `sandbox_enabled` (Boolean): Sandbox enabled
- `rate_limit_per_minute` (Integer): Rate limit per minute
- `rate_limit_per_hour` (Integer): Rate limit per hour
- `usage_count` (Integer): Usage count
- `success_count` (Integer): Success count
- `error_count` (Integer): Error count
- `avg_execution_time` (Integer): Average execution time (ms)
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- UNIQUE on `name`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `plugin_id` → `plugins.id` (SET NULL)

#### tool_executions
Stores tool execution records.

**Columns:**
- `id` (Integer, PK): Primary key
- `tool_id` (Integer, FK): Reference to tools
- `conversation_id` (Integer, FK): Reference to conversations
- `message_id` (Integer, FK): Reference to messages
- `input_data` (JSON): Input data
- `output_data` (JSON): Output data
- `status` (String): Status (pending, running, completed, failed)
- `execution_time` (Integer): Execution time (ms)
- `started_at` (DateTime): Start timestamp
- `completed_at` (DateTime): Completion timestamp
- `error_message` (Text): Error message
- `error_code` (String): Error code
- `retry_count` (Integer): Retry count
- `metadata` (JSON): Additional metadata
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `tool_id`
- FOREIGN KEY on `tool_id` → `tools.id` (CASCADE)
- FOREIGN KEY on `conversation_id` → `conversations.id` (SET NULL)
- FOREIGN KEY on `message_id` → `messages.id` (SET NULL)

### Plugin System

#### plugins
Stores plugin definitions.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `name` (String, Unique): Plugin name
- `display_name` (String): Display name
- `description` (Text): Plugin description
- `version` (String): Plugin version
- `author` (String): Plugin author
- `repository_url` (String): Repository URL
- `plugin_type` (Enum): builtin, external, marketplace
- `status` (Enum): active, inactive, deprecated, maintenance, banned
- `package_name` (String): Package name
- `package_version` (String): Package version
- `config_schema` (JSON): Configuration schema
- `default_config` (JSON): Default configuration
- `capabilities` (JSON): Capabilities
- `permissions` (JSON): Required permissions
- `dependencies` (JSON): Dependencies
- `python_dependencies` (JSON): Python dependencies
- `hooks` (JSON): Event hooks
- `install_count` (Integer): Install count
- `usage_count` (Integer): Usage count
- `rating` (Float): Rating
- `rating_count` (Integer): Rating count
- `is_featured` (Boolean): Featured status
- `is_verified` (Boolean): Verified status
- `download_count` (Integer): Download count
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- UNIQUE on `name`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### plugin_installations
Stores plugin installation records.

**Columns:**
- `id` (Integer, PK): Primary key
- `plugin_id` (Integer, FK): Reference to plugins
- `user_id` (Integer, FK): Reference to users
- `config` (JSON): User configuration
- `is_enabled` (Boolean): Enabled status
- `usage_count` (Integer): Usage count
- `last_used` (DateTime): Last usage timestamp
- `installed_at` (DateTime): Installation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `plugin_id` → `plugins.id` (CASCADE)
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

### Agent System

#### agents
Stores AI agent definitions.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `name` (String): Agent name
- `description` (Text): Agent description
- `avatar_url` (String): Avatar URL
- `agent_type` (Enum): general, specialist, orchestrator, worker
- `status` (Enum): active, inactive, busy, error
- `capabilities` (JSON): Capabilities
- `specializations` (JSON): Specializations
- `system_prompt` (Text): System prompt
- `model` (String): AI model
- `temperature` (Integer): Temperature (0-100)
- `max_tokens` (Integer): Max tokens
- `tool_ids` (JSON): Tool IDs
- `plugin_ids` (JSON): Plugin IDs
- `personality` (JSON): Personality traits
- `behavior_rules` (JSON): Behavior rules
- `constraints` (JSON): Constraints
- `memory_enabled` (Boolean): Memory enabled
- `memory_type` (String): Memory type
- `parent_agent_id` (Integer, FK): Reference to agents
- `task_count` (Integer): Task count
- `success_count` (Integer): Success count
- `error_count` (Integer): Error count
- `avg_response_time` (Integer): Average response time (ms)
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `parent_agent_id` → `agents.id` (SET NULL)

#### agent_tasks
Stores agent task records.

**Columns:**
- `id` (Integer, PK): Primary key
- `agent_id` (Integer, FK): Reference to agents
- `conversation_id` (Integer, FK): Reference to conversations
- `task_type` (String): Task type
- `description` (Text): Task description
- `input_data` (JSON): Input data
- `status` (String): Status (pending, running, completed, failed, cancelled)
- `output_data` (JSON): Output data
- `result_summary` (Text): Result summary
- `started_at` (DateTime): Start timestamp
- `completed_at` (DateTime): Completion timestamp
- `execution_time` (Integer): Execution time (ms)
- `error_message` (Text): Error message
- `error_code` (String): Error code
- `retry_count` (Integer): Retry count
- `depends_on` (JSON): Dependent task IDs
- `subtasks` (JSON): Subtask IDs
- `priority` (Integer): Priority (1-10)
- `metadata` (JSON): Additional metadata
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `agent_id`
- FOREIGN KEY on `agent_id` → `agents.id` (CASCADE)
- FOREIGN KEY on `conversation_id` → `conversations.id` (SET NULL)

#### agent_collaborations
Stores agent collaboration records.

**Columns:**
- `id` (Integer, PK): Primary key
- `conversation_id` (Integer, FK): Reference to conversations
- `agent_ids` (JSON): Agent IDs
- `orchestrator_id` (Integer, FK): Reference to agents
- `collaboration_type` (String): Collaboration type
- `workflow` (JSON): Workflow
- `communication_protocol` (JSON): Communication protocol
- `status` (String): Status
- `final_output` (JSON): Final output
- `created_at` (DateTime): Creation timestamp
- `completed_at` (DateTime): Completion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `conversation_id` → `conversations.id` (CASCADE)
- FOREIGN KEY on `orchestrator_id` → `agents.id` (SET NULL)

### Prompt System

#### prompts
Stores custom prompts.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `name` (String): Prompt name
- `description` (Text): Prompt description
- `prompt_type` (Enum): system, user, assistant, tool, few_shot
- `status` (Enum): active, archived, deprecated
- `content` (Text): Prompt content
- `variables` (JSON): Variable definitions
- `model` (String): AI model
- `temperature` (Integer): Temperature
- `max_tokens` (Integer): Max tokens
- `version` (String): Version
- `parent_prompt_id` (Integer, FK): Reference to prompts
- `category` (String): Category
- `tags` (JSON): Tags
- `usage_count` (Integer): Usage count
- `success_rate` (Integer): Success rate (0-100)
- `is_public` (Boolean): Public status
- `is_featured` (Boolean): Featured status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `parent_prompt_id` → `prompts.id` (SET NULL)

#### prompt_versions
Stores prompt version history.

**Columns:**
- `id` (Integer, PK): Primary key
- `prompt_id` (Integer, FK): Reference to prompts
- `version` (String): Version
- `content` (Text): Content
- `variables` (JSON): Variables
- `change_description` (Text): Change description
- `changed_by` (Integer, FK): Reference to users
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `prompt_id` → `prompts.id` (CASCADE)
- FOREIGN KEY on `changed_by` → `users.id` (SET NULL)

#### prompt_templates
Stores prompt templates.

**Columns:**
- `id` (Integer, PK): Primary key
- `name` (String, Unique): Template name
- `display_name` (String): Display name
- `description` (Text): Description
- `category` (String): Category
- `template` (Text): Template
- `variables` (JSON): Variable definitions
- `default_model` (String): Default model
- `default_temperature` (Integer): Default temperature
- `default_max_tokens` (Integer): Default max tokens
- `tags` (JSON): Tags
- `examples` (JSON): Examples
- `usage_count` (Integer): Usage count
- `is_active` (Boolean): Active status
- `is_featured` (Boolean): Featured status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `name`

### Document System

#### documents
Stores document metadata and content.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `file_id` (Integer, FK): Reference to files
- `title` (String): Document title
- `description` (Text): Document description
- `document_type` (Enum): pdf, docx, txt, md, html, json, csv, xlsx, pptx, code
- `status` (Enum): processing, indexed, failed, archived
- `raw_content` (Text): Raw content
- `processed_content` (Text): Processed content
- `content_hash` (String): Content hash
- `metadata` (JSON): Document metadata
- `author` (String): Author
- `language` (String): Language
- `chunk_count` (Integer): Chunk count
- `chunk_size` (Integer): Chunk size
- `chunk_overlap` (Integer): Chunk overlap
- `embedding_model` (String): Embedding model
- `vector_collection` (String): Vector collection
- `indexed_at` (DateTime): Index timestamp
- `token_count` (Integer): Token count
- `character_count` (Integer): Character count
- `is_public` (Boolean): Public status
- `access_count` (Integer): Access count
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)
- FOREIGN KEY on `file_id` → `files.id` (SET NULL)

#### document_chunks
Stores document chunks for vector search.

**Columns:**
- `id` (Integer, PK): Primary key
- `document_id` (Integer, FK): Reference to documents
- `content` (Text): Chunk content
- `chunk_index` (Integer): Chunk index
- `embedding` (JSON): Vector embedding
- `embedding_model` (String): Embedding model
- `metadata` (JSON): Metadata
- `page_number` (Integer): Page number
- `start_char` (Integer): Start character
- `end_char` (Integer): End character
- `token_count` (Integer): Token count
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `document_id`
- FOREIGN KEY on `document_id` → `documents.id` (CASCADE)

#### knowledge_bases
Stores knowledge base definitions.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `name` (String): Knowledge base name
- `description` (Text): Description
- `embedding_model` (String): Embedding model
- `chunk_size` (Integer): Chunk size
- `chunk_overlap` (Integer): Chunk overlap
- `vector_collection` (String): Vector collection
- `document_count` (Integer): Document count
- `chunk_count` (Integer): Chunk count
- `is_public` (Boolean): Public status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### knowledge_base_documents
Stores knowledge base document associations.

**Columns:**
- `id` (Integer, PK): Primary key
- `knowledge_base_id` (Integer, FK): Reference to knowledge_bases
- `document_id` (Integer, FK): Reference to documents
- `is_indexed` (Boolean): Indexed status
- `indexed_at` (DateTime): Index timestamp
- `added_at` (DateTime): Addition timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `knowledge_base_id` → `knowledge_bases.id` (CASCADE)
- FOREIGN KEY on `document_id` → `documents.id` (CASCADE)

### File System

#### files
Stores file metadata.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `filename` (String): Filename
- `original_filename` (String): Original filename
- `file_type` (Enum): image, document, code, audio, video, archive, other
- `mime_type` (String): MIME type
- `status` (Enum): uploading, processing, completed, failed, deleted
- `storage_path` (String): Storage path
- `storage_provider` (String): Storage provider
- `storage_bucket` (String): Storage bucket
- `file_size` (BigInteger): File size (bytes)
- `file_hash` (String): File hash
- `checksum` (String): Checksum
- `metadata` (JSON): File metadata
- `width` (Integer): Width (for images)
- `height` (Integer): Height (for images)
- `duration` (Integer): Duration (for audio/video)
- `is_processed` (Boolean): Processed status
- `processed_at` (DateTime): Process timestamp
- `is_public` (Boolean): Public status
- `is_encrypted` (Boolean): Encrypted status
- `encryption_key` (String): Encryption key
- `share_token` (String, Unique): Share token
- `share_expires_at` (DateTime): Share expiration
- `access_count` (Integer): Access count
- `expires_at` (DateTime): Expiration timestamp
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- UNIQUE on `share_token`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### file_versions
Stores file version history.

**Columns:**
- `id` (Integer, PK): Primary key
- `file_id` (Integer, FK): Reference to files
- `version_number` (Integer): Version number
- `storage_path` (String): Storage path
- `file_size` (BigInteger): File size
- `file_hash` (String): File hash
- `metadata` (JSON): Metadata
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `file_id` → `files.id` (CASCADE)

#### file_shares
Stores file share records.

**Columns:**
- `id` (Integer, PK): Primary key
- `file_id` (Integer, FK): Reference to files
- `shared_by` (Integer, FK): Reference to users
- `share_token` (String, Unique): Share token
- `can_download` (Boolean): Download permission
- `can_edit` (Boolean): Edit permission
- `can_delete` (Boolean): Delete permission
- `max_accesses` (Integer): Maximum accesses
- `access_count` (Integer): Access count
- `expires_at` (DateTime): Expiration timestamp
- `password_hash` (String): Password hash
- `is_active` (Boolean): Active status
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `share_token`
- FOREIGN KEY on `file_id` → `files.id` (CASCADE)
- FOREIGN KEY on `shared_by` → `users.id` (CASCADE)

### Calendar System

#### calendar_events
Stores calendar events.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `title` (String): Event title
- `description` (Text): Event description
- `location` (String): Event location
- `event_type` (Enum): meeting, appointment, reminder, task, deadline
- `status` (Enum): scheduled, confirmed, cancelled, completed, no_show
- `start_time` (DateTime): Start time
- `end_time` (DateTime): End time
- `all_day` (Boolean): All day event
- `timezone` (String): Timezone
- `recurrence_type` (Enum): none, daily, weekly, monthly, yearly, custom
- `recurrence_rule` (JSON): Recurrence rule
- `recurrence_end_date` (DateTime): Recurrence end date
- `attendees` (JSON): Attendees
- `organizer` (String): Organizer
- `external_event_id` (String): External event ID
- `external_calendar` (String): External calendar
- `sync_status` (String): Sync status
- `reminders` (JSON): Reminders
- `reminder_sent` (Boolean): Reminder sent
- `meeting_link` (String): Meeting link
- `meeting_password` (String): Meeting password
- `conference_provider` (String): Conference provider
- `metadata` (JSON): Metadata
- `tags` (JSON): Tags
- `priority` (Integer): Priority (1-10)
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `deleted_at` (DateTime): Soft deletion timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### calendar_integrations
Stores calendar integration settings.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `google_enabled` (Boolean): Google Calendar enabled
- `google_token` (Text): Google token
- `google_refresh_token` (Text): Google refresh token
- `google_calendar_id` (String): Google calendar ID
- `google_sync_enabled` (Boolean): Google sync enabled
- `outlook_enabled` (Boolean): Outlook enabled
- `outlook_token` (Text): Outlook token
- `outlook_refresh_token` (Text): Outlook refresh token
- `outlook_calendar_id` (String): Outlook calendar ID
- `outlook_sync_enabled` (Boolean): Outlook sync enabled
- `sync_direction` (String): Sync direction
- `sync_frequency` (Integer): Sync frequency (seconds)
- `last_sync_at` (DateTime): Last sync timestamp
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

### Notification System

#### notifications
Stores notification records.

**Columns:**
- `id` (Integer, PK): Primary key
- `uuid` (String, Unique): UUID for external references
- `user_id` (Integer, FK): Reference to users
- `title` (String): Notification title
- `message` (Text): Notification message
- `notification_type` (Enum): info, success, warning, error, task, reminder, system
- `channels` (JSON): Channels
- `preferred_channel` (Enum): in_app, email, sms, push, webhook
- `status` (Enum): pending, sent, delivered, failed, read, dismissed
- `priority` (Integer): Priority (1-10)
- `is_urgent` (Boolean): Urgent status
- `action_url` (String): Action URL
- `action_label` (String): Action label
- `metadata` (JSON): Metadata
- `category` (String): Category
- `tags` (JSON): Tags
- `sent_at` (DateTime): Sent timestamp
- `delivered_at` (DateTime): Delivered timestamp
- `read_at` (DateTime): Read timestamp
- `error_message` (Text): Error message
- `retry_count` (Integer): Retry count
- `expires_at` (DateTime): Expiration timestamp
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `uuid`
- INDEX on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### notification_preferences
Stores user notification preferences.

**Columns:**
- `id` (Integer, PK): Primary key
- `user_id` (Integer, FK): Reference to users
- `in_app_enabled` (Boolean): In-app enabled
- `email_enabled` (Boolean): Email enabled
- `sms_enabled` (Boolean): SMS enabled
- `push_enabled` (Boolean): Push enabled
- `webhook_enabled` (Boolean): Webhook enabled
- `info_enabled` (Boolean): Info enabled
- `success_enabled` (Boolean): Success enabled
- `warning_enabled` (Boolean): Warning enabled
- `error_enabled` (Boolean): Error enabled
- `task_enabled` (Boolean): Task enabled
- `reminder_enabled` (Boolean): Reminder enabled
- `system_enabled` (Boolean): System enabled
- `quiet_hours_enabled` (Boolean): Quiet hours enabled
- `quiet_hours_start` (String): Quiet hours start
- `quiet_hours_end` (String): Quiet hours end
- `quiet_hours_timezone` (String): Quiet hours timezone
- `email_digest` (Boolean): Email digest
- `email_digest_frequency` (String): Email digest frequency
- `webhook_url` (String): Webhook URL
- `webhook_secret` (String): Webhook secret
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `user_id`
- FOREIGN KEY on `user_id` → `users.id` (CASCADE)

#### notification_templates
Stores notification templates.

**Columns:**
- `id` (Integer, PK): Primary key
- `name` (String, Unique): Template name
- `display_name` (String): Display name
- `description` (Text): Description
- `category` (String): Category
- `title_template` (String): Title template
- `message_template` (Text): Message template
- `variables` (JSON): Variable definitions
- `notification_type` (Enum): Notification type
- `default_channels` (JSON): Default channels
- `priority` (Integer): Priority
- `action_url_template` (String): Action URL template
- `action_label_template` (String): Action label template
- `is_active` (Boolean): Active status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `name`

## Migration Strategy

### Initial Migration
The initial migration creates all tables with their indexes, foreign keys, and enums.

### Future Migrations
All schema changes should be done through Alembic migrations:
1. Create new migration: `alembic revision --autogenerate -m "description"`
2. Review generated migration
3. Apply migration: `alembic upgrade head`
4. Rollback if needed: `alembic downgrade -1`

## Performance Considerations

### Indexing Strategy
- All foreign keys are indexed
- All unique fields have unique indexes
- Frequently queried fields have indexes
- Composite indexes for complex queries

### Query Optimization
- Use `select_related` for relationships
- Use `prefetch_related` for many-to-many
- Implement query result caching with Redis
- Use connection pooling

### Data Archival
- Implement soft deletes with `deleted_at`
- Archive old data to separate tables
- Implement data retention policies
- Use partitioning for large tables

## Security Considerations

### Data Protection
- All passwords are hashed with bcrypt
- Sensitive data is encrypted at rest
- API keys are stored securely
- Session tokens have expiration

### Access Control
- Row-level security via user_id
- Role-based access control
- API key scoping
- Rate limiting per user/key

### Audit Trail
- All tables have created_at/updated_at
- Track who changed data
- Log all sensitive operations
- Implement audit logging

## Backup Strategy

### Backup Frequency
- Daily full backups
- Hourly incremental backups
- Real-time WAL archiving

### Backup Retention
- Keep daily backups for 30 days
- Keep weekly backups for 12 weeks
- Keep monthly backups for 12 months

### Disaster Recovery
- Geographic replication
- Point-in-time recovery
- Automated failover
- Regular restore testing
