import { request } from "../request";

export interface LocalizedText {
  zh: string;
  en: string;
}

export interface ManagedQuickPrompt {
  title: LocalizedText;
  description: LocalizedText;
  prompt: LocalizedText;
  color: string;
  icon_name?: string | null;
}

export interface ManagedZdxTemplate {
  id: string;
  version: string;
  label: LocalizedText;
  description: LocalizedText;
  welcome_message: LocalizedText;
  soul: string;
  quick_prompts: ManagedQuickPrompt[];
  task_examples: { zh: string[]; en: string[] };
  builtin_skill_slugs: string[];
  skill_package_ids: string[];
  available_builtin_skills: string[];
  available_skill_packages: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  managed_model: Record<string, unknown>;
}

export const managedTemplatesApi = {
  get(): Promise<ManagedZdxTemplate> {
    return request<ManagedZdxTemplate>(
      "/managed-experts/tonglian-fazai/template",
    );
  },
  update(
    template: Pick<
      ManagedZdxTemplate,
      | "label"
      | "description"
      | "welcome_message"
      | "soul"
      | "quick_prompts"
      | "task_examples"
      | "builtin_skill_slugs"
      | "skill_package_ids"
      | "managed_model"
    >,
  ): Promise<ManagedZdxTemplate> {
    return request<ManagedZdxTemplate>(
      "/managed-experts/tonglian-fazai/template",
      {
        method: "PUT",
        body: JSON.stringify(template),
      },
    );
  },
  publish(): Promise<{
    template: ManagedZdxTemplate;
    updated: number;
    reloaded: number;
    reload_failed: number;
    sync_failed: number;
    pending: number;
    skill_packages_skipped: number;
  }> {
    return request("/managed-experts/tonglian-fazai/template/publish", {
      method: "POST",
    });
  },
};
