-- Schema v16: managed agent metadata for system-provisioned agents.

ALTER TABLE agents ADD COLUMN IF NOT EXISTS managed_type TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS config_locked INTEGER NOT NULL DEFAULT 0;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS template_version TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_user_managed_type
  ON agents(user_id, managed_type)
  WHERE user_id IS NOT NULL AND managed_type IS NOT NULL;

UPDATE _schema_version SET version = 16;
