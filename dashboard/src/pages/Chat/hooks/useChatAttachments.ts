import { useCallback, useRef, useState } from "react";
import type { ChangeEvent, ClipboardEvent, DragEvent } from "react";
import { useTranslation } from "react-i18next";
import { uploadFile } from "../../../api/modules/upload";
import { agentAttachmentAccessUrl } from "../../../utils/toolMediaBlocks";
import type { ChatAttachment } from "./useChat";
import { message as antMessage } from "@/utils/antdMessage";
import { apiErrorMessage } from "../../../utils/apiError";

import { inferAttachmentKind } from "../utils/chatAttachments";
import { useServerUploadLimit } from "../../../hooks/useServerUploadLimit";

export function useChatAttachments(
  agentId: string | null | undefined,
  enabled = true,
) {
  const { t } = useTranslation();
  const { maxUploadBytes, maxUploadMb } = useServerUploadLimit();
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback(
    async (files: FileList | File[]) => {
      if (!enabled) return;

      const fileArr = Array.from(files).filter((f) => {
        if (f.size > maxUploadBytes) {
          antMessage.error(
            t("upload.tooLarge", "File too large (max {{maxMb}}MB): {{name}}", {
              name: f.name,
              maxMb: maxUploadMb,
            }),
          );
          return false;
        }
        return true;
      });

      if (fileArr.length === 0) return;

      if (!agentId) {
        antMessage.error(t("upload.failed", "Upload failed"));
        return;
      }

      setUploading(true);
      try {
        const results = await Promise.all(
          fileArr.map(async (file) => {
            const res = await uploadFile(agentId, file);
            const workspacePath = res.path || res.workspace_path;
            const previewUrl =
              res.access_url ||
              res.url ||
              (workspacePath
                ? agentAttachmentAccessUrl(
                    agentId,
                    workspacePath,
                    res.media_type,
                  )
                : "");
            return {
              url: previewUrl,
              filename: res.filename,
              mediaType: res.media_type,
              workspacePath,
              kind: inferAttachmentKind(file, res.media_type),
            } satisfies ChatAttachment;
          }),
        );
        setAttachments((prev) => [...prev, ...results]);
      } catch (err: unknown) {
        antMessage.error(
          apiErrorMessage(err, t("upload.failed", "Upload failed"), t),
        );
      } finally {
        setUploading(false);
      }
    },
    [agentId, enabled, maxUploadBytes, maxUploadMb, t],
  );

  const handleFileSelect = useCallback(() => {
    if (!enabled) return;
    fileInputRef.current?.click();
  }, [enabled]);

  const handleFileChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        void processFiles(e.target.files);
      }
      e.target.value = "";
    },
    [processFiles],
  );

  const removeAttachment = useCallback((index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearAttachments = useCallback(() => {
    setAttachments([]);
  }, []);

  const restoreAttachments = useCallback((next: ChatAttachment[]) => {
    setAttachments(next.map((a) => ({ ...a })));
  }, []);

  const handlePaste = useCallback(
    (e: ClipboardEvent) => {
      if (!enabled) return;

      const items = e.clipboardData?.items;
      if (!items) return;
      const pastedFiles: File[] = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.kind === "file") {
          const file = item.getAsFile();
          if (file) pastedFiles.push(file);
        }
      }
      if (pastedFiles.length > 0) {
        e.preventDefault();
        void processFiles(pastedFiles);
      }
    },
    [enabled, processFiles],
  );

  const handleDragEnter = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;

      e.preventDefault();
      e.stopPropagation();
      setDragOver(true);
    },
    [enabled],
  );

  const handleDragLeave = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;

      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
    },
    [enabled],
  );

  const handleDragOver = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;

      e.preventDefault();
      e.stopPropagation();
    },
    [enabled],
  );

  const handleDrop = useCallback(
    (e: DragEvent) => {
      if (!enabled) return;

      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        void processFiles(e.dataTransfer.files);
      }
    },
    [enabled, processFiles],
  );

  return {
    attachments,
    uploading,
    dragOver,
    fileInputRef,
    processFiles,
    handleFileSelect,
    handleFileChange,
    removeAttachment,
    clearAttachments,
    restoreAttachments,
    handlePaste,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
  };
}
