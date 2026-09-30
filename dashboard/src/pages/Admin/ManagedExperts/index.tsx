import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Input,
  Select,
  Space,
  Typography,
  message,
} from "antd";
import { Plus, Save, Send, Trash2 } from "lucide-react";
import PageShell from "../../../layouts/PageShell";
import {
  managedTemplatesApi,
  type ManagedZdxTemplate,
} from "../../../api/modules/managedTemplates";
import { useTranslation } from "react-i18next";

const { TextArea } = Input;

export default function ManagedExpertsPage() {
  const { t } = useTranslation();
  const [template, setTemplate] = useState<ManagedZdxTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [form] = Form.useForm();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const value = await managedTemplatesApi.get();
      setTemplate(value);
      form.setFieldsValue(value);
    } finally {
      setLoading(false);
    }
  }, [form]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      const value = await managedTemplatesApi.update(values);
      setTemplate(value);
      form.setFieldsValue(value);
      message.success(t("managedExperts.saved"));
    } finally {
      setSaving(false);
    }
  };

  const publish = async () => {
    setPublishing(true);
    try {
      const result = await managedTemplatesApi.publish();
      message.success(
        t("managedExperts.published", {
          updated: result.updated,
          reloaded: result.reloaded,
          reloadFailed: result.reload_failed,
        }),
      );
      await load();
    } finally {
      setPublishing(false);
    }
  };

  return (
    <PageShell
      title={t("pageShell.managedExperts.title")}
      subtitle={t("pageShell.managedExperts.subtitle")}
    >
      <Card loading={loading}>
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Alert type="info" showIcon message={t("managedExperts.warning")} />
          <Typography.Text type="secondary">
            {t("managedExperts.version", { version: template?.version ?? "-" })}
          </Typography.Text>
          <Form form={form} layout="vertical">
            <Form.Item
              label={t("managedExperts.labelZh")}
              name={["label", "zh"]}
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.labelEn")}
              name={["label", "en"]}
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.descriptionZh")}
              name={["description", "zh"]}
            >
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.descriptionEn")}
              name={["description", "en"]}
            >
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.welcomeZh")}
              name={["welcome_message", "zh"]}
            >
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.welcomeEn")}
              name={["welcome_message", "en"]}
            >
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.soul")}
              name="soul"
              rules={[{ required: true }]}
            >
              <TextArea rows={18} />
            </Form.Item>
            <Typography.Title level={5}>
              {t("managedExperts.quickPrompts")}
            </Typography.Title>
            <Form.List name="quick_prompts">
              {(fields, { add, remove }) => (
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  {fields.map((field, index) => (
                    <Card
                      key={field.key}
                      size="small"
                      title={`${t("managedExperts.quickPrompt")} ${index + 1}`}
                      extra={
                        <Button
                          danger
                          type="text"
                          icon={<Trash2 size={15} />}
                          aria-label={t("managedExperts.removeQuickPrompt")}
                          onClick={() => remove(field.name)}
                        />
                      }
                    >
                      <Space direction="vertical" style={{ width: "100%" }}>
                        <Space wrap style={{ width: "100%" }}>
                          <Form.Item
                            label={t("managedExperts.promptTitleZh")}
                            name={[field.name, "title", "zh"]}
                            rules={[{ required: true }]}
                          >
                            <Input />
                          </Form.Item>
                          <Form.Item
                            label={t("managedExperts.promptTitleEn")}
                            name={[field.name, "title", "en"]}
                            rules={[{ required: true }]}
                          >
                            <Input />
                          </Form.Item>
                        </Space>
                        <Form.Item
                          label={t("managedExperts.promptDescriptionZh")}
                          name={[field.name, "description", "zh"]}
                        >
                          <Input />
                        </Form.Item>
                        <Form.Item
                          label={t("managedExperts.promptDescriptionEn")}
                          name={[field.name, "description", "en"]}
                        >
                          <Input />
                        </Form.Item>
                        <Form.Item
                          label={t("managedExperts.promptZh")}
                          name={[field.name, "prompt", "zh"]}
                          rules={[{ required: true }]}
                        >
                          <TextArea rows={2} />
                        </Form.Item>
                        <Form.Item
                          label={t("managedExperts.promptEn")}
                          name={[field.name, "prompt", "en"]}
                          rules={[{ required: true }]}
                        >
                          <TextArea rows={2} />
                        </Form.Item>
                      </Space>
                    </Card>
                  ))}
                  <Button
                    type="dashed"
                    icon={<Plus size={15} />}
                    onClick={() =>
                      add({
                        title: { zh: "", en: "" },
                        description: { zh: "", en: "" },
                        prompt: { zh: "", en: "" },
                        color: "#e8f4ff",
                        icon_name: null,
                      })
                    }
                  >
                    {t("managedExperts.addQuickPrompt")}
                  </Button>
                </Space>
              )}
            </Form.List>
            <Typography.Title level={5}>
              {t("managedExperts.taskExamples")}
            </Typography.Title>
            <Form.Item
              label={t("managedExperts.taskExamplesZh")}
              name={["task_examples", "zh"]}
            >
              <Select mode="tags" tokenSeparators={["\n"]} />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.taskExamplesEn")}
              name={["task_examples", "en"]}
            >
              <Select mode="tags" tokenSeparators={["\n"]} />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.builtinSkills")}
              name="builtin_skill_slugs"
            >
              <Checkbox.Group
                options={(template?.available_builtin_skills ?? []).map(
                  (slug) => ({ label: slug, value: slug }),
                )}
              />
            </Form.Item>
            <Form.Item
              label={t("managedExperts.marketSkills")}
              name="skill_package_ids"
            >
              {(template?.available_skill_packages ?? []).length > 0 ? (
                <Select
                  mode="multiple"
                  options={template?.available_skill_packages.map((pack) => ({
                    label: pack.name,
                    value: pack.id,
                  }))}
                />
              ) : (
                <Typography.Text type="secondary">
                  {t("managedExperts.noMarketSkills")}
                </Typography.Text>
              )}
            </Form.Item>
          </Form>
          <Space>
            <Button
              icon={<Save size={16} />}
              loading={saving}
              onClick={() => void save()}
            >
              {t("managedExperts.save")}
            </Button>
            <Button
              type="primary"
              icon={<Send size={16} />}
              loading={publishing}
              onClick={() => void publish()}
            >
              {t("managedExperts.publish")}
            </Button>
          </Space>
        </Space>
      </Card>
    </PageShell>
  );
}
