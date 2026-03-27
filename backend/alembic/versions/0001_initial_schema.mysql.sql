-- MindWise initial schema for MySQL / phpMyAdmin
-- Source revision: 0001_initial_schema
-- Run this in phpMyAdmin's SQL editor.
-- If needed, change the database name before running.

CREATE DATABASE IF NOT EXISTS `mindwise`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `mindwise`;

CREATE TABLE IF NOT EXISTS `users` (
  `id` VARCHAR(36) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `full_name` VARCHAR(255) NULL,
  `picture_url` VARCHAR(500) NULL,
  `provider_subject` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(50) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_provider_subject` (`provider_subject`),
  KEY `ix_users_email` (`email`),
  KEY `ix_users_provider_subject` (`provider_subject`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `projects` (
  `id` VARCHAR(36) NOT NULL,
  `user_id` VARCHAR(36) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `prompt` TEXT NOT NULL,
  `source_type` ENUM('prompt', 'document', 'lesson_request') NOT NULL,
  `source_document_path` VARCHAR(500) NULL,
  `requested_duration_minutes` INT NOT NULL,
  `visual_style` ENUM(
    'clean_academic',
    'modern_infographic',
    'cinematic_technical',
    'playful_educational',
    'startup_explainer'
  ) NOT NULL,
  `topic_domain` VARCHAR(128) NULL,
  `status` ENUM('draft', 'active', 'completed', 'failed') NOT NULL,
  `scene_plan_version` INT NOT NULL,
  `metadata_json` JSON NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_projects_title` (`title`),
  KEY `ix_projects_user_id` (`user_id`),
  CONSTRAINT `fk_projects_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `video_jobs` (
  `id` VARCHAR(36) NOT NULL,
  `project_id` VARCHAR(36) NOT NULL,
  `job_type` ENUM('full_render', 'preview') NOT NULL,
  `status` ENUM(
    'pending',
    'planning',
    'queued',
    'running',
    'composing',
    'completed',
    'failed',
    'canceled'
  ) NOT NULL,
  `target_resolution` VARCHAR(32) NOT NULL,
  `requested_duration_seconds` INT NOT NULL,
  `llm_provider` VARCHAR(64) NOT NULL,
  `tts_provider` VARCHAR(64) NOT NULL,
  `image_generation_enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `progress_pct` FLOAT NOT NULL,
  `render_plan_json` JSON NOT NULL,
  `current_step` VARCHAR(128) NULL,
  `retry_count` INT NOT NULL,
  `started_at` DATETIME(6) NULL,
  `completed_at` DATETIME(6) NULL,
  `failed_at` DATETIME(6) NULL,
  `error_message` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_video_jobs_project_id` (`project_id`),
  KEY `ix_video_jobs_status` (`status`),
  CONSTRAINT `fk_video_jobs_project_id`
    FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `output_files` (
  `id` VARCHAR(36) NOT NULL,
  `project_id` VARCHAR(36) NOT NULL,
  `job_id` VARCHAR(36) NULL,
  `scene_id` VARCHAR(36) NULL,
  `file_type` ENUM('scene_video', 'final_video', 'audio', 'subtitle', 'diagnostics') NOT NULL,
  `storage_path` VARCHAR(500) NOT NULL,
  `mime_type` VARCHAR(128) NOT NULL,
  `duration_seconds` FLOAT NULL,
  `width` INT NULL,
  `height` INT NULL,
  `size_bytes` INT NULL,
  `checksum` VARCHAR(128) NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_output_files_project_id` (`project_id`),
  KEY `ix_output_files_job_id` (`job_id`),
  KEY `ix_output_files_scene_id` (`scene_id`),
  CONSTRAINT `fk_output_files_project_id`
    FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_output_files_job_id`
    FOREIGN KEY (`job_id`) REFERENCES `video_jobs` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `scene_specs` (
  `id` VARCHAR(36) NOT NULL,
  `project_id` VARCHAR(36) NOT NULL,
  `job_id` VARCHAR(36) NOT NULL,
  `order_index` INT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `scene_type` VARCHAR(64) NOT NULL,
  `learning_objective` TEXT NOT NULL,
  `narration_text` TEXT NOT NULL,
  `estimated_duration_seconds` FLOAT NOT NULL,
  `renderer_key` VARCHAR(64) NOT NULL,
  `spec_json` JSON NOT NULL,
  `status` ENUM('pending', 'ready', 'rendering', 'completed', 'failed', 'skipped') NOT NULL,
  `checksum` VARCHAR(128) NULL,
  `output_file_id` VARCHAR(36) NULL,
  `last_error` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_scene_specs_project_id` (`project_id`),
  KEY `ix_scene_specs_job_id` (`job_id`),
  KEY `ix_scene_specs_order_index` (`order_index`),
  KEY `ix_scene_specs_output_file_id` (`output_file_id`),
  CONSTRAINT `fk_scene_specs_project_id`
    FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_scene_specs_job_id`
    FOREIGN KEY (`job_id`) REFERENCES `video_jobs` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_scene_specs_output_file_id`
    FOREIGN KEY (`output_file_id`) REFERENCES `output_files` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `output_files`
  ADD CONSTRAINT `fk_output_files_scene_id`
  FOREIGN KEY (`scene_id`) REFERENCES `scene_specs` (`id`)
  ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS `auth_sessions` (
  `id` VARCHAR(36) NOT NULL,
  `user_id` VARCHAR(36) NOT NULL,
  `provider` VARCHAR(50) NOT NULL,
  `refresh_token_hash` VARCHAR(255) NOT NULL,
  `access_token_expires_at` DATETIME(6) NULL,
  `user_agent` VARCHAR(255) NULL,
  `ip_address` VARCHAR(64) NULL,
  `state_nonce` VARCHAR(255) NULL,
  `last_used_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_auth_sessions_refresh_token_hash` (`refresh_token_hash`),
  KEY `ix_auth_sessions_user_id` (`user_id`),
  CONSTRAINT `fk_auth_sessions_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `render_attempts` (
  `id` VARCHAR(36) NOT NULL,
  `job_id` VARCHAR(36) NOT NULL,
  `scene_id` VARCHAR(36) NULL,
  `attempt_type` VARCHAR(64) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `worker_name` VARCHAR(128) NULL,
  `log_excerpt` TEXT NULL,
  `started_at` DATETIME(6) NULL,
  `completed_at` DATETIME(6) NULL,
  `error_message` TEXT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_render_attempts_job_id` (`job_id`),
  KEY `ix_render_attempts_scene_id` (`scene_id`),
  CONSTRAINT `fk_render_attempts_job_id`
    FOREIGN KEY (`job_id`) REFERENCES `video_jobs` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_render_attempts_scene_id`
    FOREIGN KEY (`scene_id`) REFERENCES `scene_specs` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `assets` (
  `id` VARCHAR(36) NOT NULL,
  `project_id` VARCHAR(36) NULL,
  `job_id` VARCHAR(36) NULL,
  `scene_id` VARCHAR(36) NULL,
  `asset_type` ENUM('image', 'icon', 'audio', 'subtitle', 'plot', 'document', 'video') NOT NULL,
  `provider` VARCHAR(64) NOT NULL,
  `source_url` VARCHAR(500) NULL,
  `local_path` VARCHAR(500) NULL,
  `checksum` VARCHAR(128) NULL,
  `metadata_json` JSON NOT NULL,
  `status` ENUM('pending', 'ready', 'failed') NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `updated_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_assets_project_id` (`project_id`),
  KEY `ix_assets_job_id` (`job_id`),
  KEY `ix_assets_scene_id` (`scene_id`),
  CONSTRAINT `fk_assets_project_id`
    FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_assets_job_id`
    FOREIGN KEY (`job_id`) REFERENCES `video_jobs` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_assets_scene_id`
    FOREIGN KEY (`scene_id`) REFERENCES `scene_specs` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `log_entries` (
  `id` VARCHAR(36) NOT NULL,
  `job_id` VARCHAR(36) NULL,
  `scene_id` VARCHAR(36) NULL,
  `level` VARCHAR(16) NOT NULL,
  `event` VARCHAR(128) NOT NULL,
  `message` TEXT NOT NULL,
  `payload_json` JSON NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_log_entries_job_id` (`job_id`),
  KEY `ix_log_entries_scene_id` (`scene_id`),
  CONSTRAINT `fk_log_entries_job_id`
    FOREIGN KEY (`job_id`) REFERENCES `video_jobs` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_log_entries_scene_id`
    FOREIGN KEY (`scene_id`) REFERENCES `scene_specs` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `usage_stats` (
  `id` VARCHAR(36) NOT NULL,
  `user_id` VARCHAR(36) NULL,
  `project_id` VARCHAR(36) NULL,
  `job_id` VARCHAR(36) NULL,
  `provider` VARCHAR(64) NOT NULL,
  `metric_name` VARCHAR(64) NOT NULL,
  `metric_value` FLOAT NOT NULL,
  `unit` VARCHAR(32) NOT NULL,
  `recorded_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_usage_stats_user_id` (`user_id`),
  KEY `ix_usage_stats_project_id` (`project_id`),
  KEY `ix_usage_stats_job_id` (`job_id`),
  CONSTRAINT `fk_usage_stats_user_id`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE SET NULL,
  CONSTRAINT `fk_usage_stats_project_id`
    FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_usage_stats_job_id`
    FOREIGN KEY (`job_id`) REFERENCES `video_jobs` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `alembic_version` (
  `version_num` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `alembic_version` (`version_num`)
VALUES ('0001_initial_schema')
ON DUPLICATE KEY UPDATE `version_num` = VALUES(`version_num`);
