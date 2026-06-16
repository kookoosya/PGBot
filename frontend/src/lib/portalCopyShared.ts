/**
 * Общие тексты портала — shared/portal_copy.json
 * (синхрон с backend/app/constants/portal_copy.py)
 */
import copy from "../../../shared/portal_copy.json";

export const PORTAL_COPY_BRAND = copy.brand;

export const ISSUE_STATUS_HINTS: Record<string, string> = copy.issue_status_hints;

export const ISSUE_STATUS_EMOJI: Record<string, string> = copy.issue_status_emoji;

export const PORTAL_COPY_LINKS = copy.links;

export const PORTAL_COPY_VK = copy.vk;

export type EmptyStateCopy = {
  icon: string;
  title: string;
  text: string;
};

export const EMPTY_STATES = copy.empty_states as Record<string, EmptyStateCopy>;
