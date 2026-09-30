import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { SlashCommandSpec } from "../../../api/modules/slash";
import type { SkillSpec } from "../../Agent/Skills/useSkills";
import { useSlashMentionInput } from "./useSlashMentionInput";

const stopCommand: SlashCommandSpec = {
  name: "stop",
  command: "/stop",
  aliases: [],
  label_en: "Stop",
  label_zh: "停止",
  description_en: "",
  description_zh: "",
  usage: "/stop",
  icon: "Square",
  tone: "red",
  category: "core",
  origins: ["ui"],
  client_action: "cancel_stream",
};

const optionalSkillsCommand: SlashCommandSpec = {
  name: "skills",
  command: "/skills",
  aliases: [],
  label_en: "Skills",
  label_zh: "技能",
  description_en: "List skills",
  description_zh: "列出技能",
  usage: "/skills [list]",
  icon: "Sparkles",
  tone: "amber",
  category: "system",
  origins: ["ui"],
  client_action: "none",
};

function skill(over: Partial<SkillSpec> = {}): SkillSpec {
  return {
    slug: "web-search",
    name: "Web Search",
    description: "Search",
    enabled: true,
    kind: "builtin",
    ...over,
  };
}

describe("useSlashMentionInput skills", () => {
  it("lists enabled skills with friendly labels and skips reserved slash names", () => {
    const { result } = renderHook(() =>
      useSlashMentionInput({
        text: "",
        setText: vi.fn(),
        textareaRef: { current: null },
        slashCommands: [stopCommand],
        labelFor: (spec) => spec.label_en,
        locale: "en",
        availableSkills: [
          skill(),
          skill({ slug: "stop", name: "Stop skill", enabled: true }),
          skill({ slug: "off", name: "Off", enabled: false }),
        ],
        availableExperts: [],
        selectedConnectors: [],
        onSend: vi.fn(),
        onNewChat: vi.fn(),
        onCancel: vi.fn(),
        isStreaming: false,
        onSubmitRef: { current: vi.fn() },
      }),
    );

    expect(result.current.slashMenuItems.map((item) => item.command)).toEqual([
      "/stop",
      "✦ Web Search",
    ]);
    const skillItem = result.current.slashMenuItems.find(
      (item) => item.spec.name === "web-search",
    );
    expect(skillItem?.label).toBe("Web Search");
    expect(skillItem?.spec.usage).toBe("✦ Web Search <task>");
    expect(skillItem?.spec.category).toBe("skills");
  });

  it("sends the command instead of its optional-argument usage hint", () => {
    const onSend = vi.fn();
    const { result } = renderHook(() =>
      useSlashMentionInput({
        text: "",
        setText: vi.fn(),
        textareaRef: { current: null },
        slashCommands: [optionalSkillsCommand],
        labelFor: (spec) => spec.label_en,
        locale: "en",
        availableExperts: [],
        selectedConnectors: [],
        onSend,
        onNewChat: vi.fn(),
        onCancel: vi.fn(),
        isStreaming: false,
        onSubmitRef: { current: vi.fn() },
      }),
    );

    const item = result.current.slashMenuItems[0];
    expect(item.command).toBe("/skills");
    expect(item.displayCommand).toBe("/skills [list]");

    act(() => result.current.handleTextChange(""));
    act(() => result.current.handleSlashSelect(item.command));
    expect(onSend).toHaveBeenCalledWith("/skills");
  });
});

describe("useSlashMentionInput workspace files", () => {
  it("keeps empty @ as a hint-only file section and inserts the workspace path", () => {
    const setText = vi.fn();
    const { result } = renderHook(() =>
      useSlashMentionInput({
        text: "@",
        setText,
        textareaRef: { current: null },
        slashCommands: [stopCommand],
        labelFor: (spec) => spec.label_en,
        locale: "en",
        availableExperts: [],
        selectedConnectors: [],
        agentId: "A1",
        onSend: vi.fn(),
        onNewChat: vi.fn(),
        onCancel: vi.fn(),
        isStreaming: false,
        onSubmitRef: { current: vi.fn() },
      }),
    );

    expect(result.current.mentionItems).toEqual([]);

    act(() => {
      result.current.handleTextChange("@");
    });
    act(() => {
      result.current.handleMentionSelect({
        kind: "file",
        path: "docs/api.md",
        label: "api.md",
      });
    });

    expect(setText).toHaveBeenCalledWith("@docs/api.md ");
  });

  it("keeps spaces in the workspace path and does not toggle an existing cite", () => {
    const setText = vi.fn();
    const { result } = renderHook(() =>
      useSlashMentionInput({
        text: "@docs/api.md @note",
        setText,
        textareaRef: { current: null },
        slashCommands: [stopCommand],
        labelFor: (spec) => spec.label_en,
        locale: "en",
        availableExperts: [],
        selectedConnectors: [],
        agentId: "A1",
        onSend: vi.fn(),
        onNewChat: vi.fn(),
        onCancel: vi.fn(),
        isStreaming: false,
        onSubmitRef: { current: vi.fn() },
      }),
    );

    act(() => {
      result.current.handleTextChange("@docs/api.md @note");
    });
    act(() => {
      result.current.handleMentionSelect({
        kind: "file",
        path: "notes/my file.md",
        label: "my file.md",
      });
    });

    expect(setText).toHaveBeenCalledWith("@docs/api.md @notes/my file.md ");
  });
});
