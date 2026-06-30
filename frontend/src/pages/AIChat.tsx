import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiteraryInlineLoader } from "@/components/literary";
import { Button } from "@/components/ui/button";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { api } from "@/lib/api/index";
import type { AIModelOption, AIStatus, ChatMessage, UsageInfo } from "@/lib/api/types/ai";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

type Tab = "chat" | "image";

const copy = PAGE_SECTIONS.ai;

const FLOW_STEPS = [
  { icon: "💬", title: "Спросите", text: "Туризм, объявления, стихи — на русском." },
  { icon: "🎨", title: "Нарисуйте", text: "Вкладка «Картинки» — описание на русском." },
  { icon: "📊", title: "Лимит", text: "Бесплатные запросы обновляются каждый день." },
];

const CHAT_SUGGESTIONS = [
  "Напиши объявление про дрова",
  "Что посмотреть в Пушкиногорье?",
  "Напиши короткое стихотворение про зиму",
];

const IMAGE_SUGGESTIONS = [
  "Усадьба в русском стиле, закат",
  "Памятник Пушкину в парке",
  "Уютная изба в снегу",
];

export function AIChat() {
  useDocumentTitle(copy.title);

  const [tab, setTab] = useState<Tab>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Здравствуйте! Я помощник Пушкиногорья — подскажу про музеи, напишу объявление или стих. Спросите что угодно — или нарисуйте картинку во вкладке «Картинки».",
    },
  ]);
  const [input, setInput] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState(false);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [chatModels, setChatModels] = useState<AIModelOption[]>([]);
  const [imageModels, setImageModels] = useState<AIModelOption[]>([]);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [chatModel, setChatModel] = useState("gemini-flash");
  const [imageModel, setImageModel] = useState("flux");
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [imageProvider, setImageProvider] = useState<string | null>(null);
  const [imageError, setImageError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadModels = () => {
    setModelsLoading(true);
    setModelsError(false);
    Promise.all([api.getAIUsage(), api.getAIModels()])
      .then(([usageRes, modelsRes]) => {
        setUsage(usageRes);
        setChatModels(modelsRes.chat_models);
        setImageModels(modelsRes.image_models);
        if (modelsRes.status) setAiStatus(modelsRes.status);
        const preferred = modelsRes.chat_models.find((x) => x.id === "gemini-flash") || modelsRes.chat_models[0];
        if (preferred) setChatModel(preferred.id);
        if (modelsRes.image_models[0]) setImageModel(modelsRes.image_models[0].id);
      })
      .catch(() => setModelsError(true))
      .finally(() => setModelsLoading(false));
  };

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const limitReached = usage !== null && usage.remaining <= 0;

  const send = async () => {
    if (!input.trim() || loading || limitReached) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const history = messages
        .filter((m) => m.role !== "system")
        .map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.content }));
      const res = await api.sendAIChat(userMsg, history, chatModel);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      setUsage({ used: res.daily_limit - res.remaining, remaining: res.remaining, daily_limit: res.daily_limit });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка. Попробуйте позже.";
      setMessages((m) => [...m, { role: "assistant", content: `⚠️ ${msg}` }]);
    } finally {
      setLoading(false);
    }
  };

  const generateImage = async () => {
    if (!imagePrompt.trim() || imageLoading) return;
    setImageLoading(true);
    setImageError("");
    setGeneratedImage(null);
    setImageProvider(null);
    try {
      const res = await api.generateAIImage(imagePrompt.trim(), imageModel);
      if (res.error || !res.url) {
        setImageError(res.error || "Не удалось сгенерировать");
      } else {
        setGeneratedImage(`${res.url}?t=${Date.now()}`);
        setImageProvider(res.provider || null);
      }
      api.getAIUsage().then(setUsage).catch(console.error);
    } catch (e) {
      setImageError(e instanceof Error ? e.message : "Ошибка генерации");
    } finally {
      setImageLoading(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-3xl ai-page">
      <PageHeader icon="🤖" title={copy.title} subtitle={copy.lead} />

      <section className="page-panel page-panel--gold mb-4" aria-label="Возможности ИИ">
        <div className="complaints-flow">
          {FLOW_STEPS.map((step) => (
            <div key={step.title} className="complaints-flow-step">
              <span className="complaints-flow-icon" aria-hidden>{step.icon}</span>
              <div>
                <p className="complaints-flow-title m-0">{step.title}</p>
                <p className="complaints-flow-text m-0">{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {usage && (
        <div className="page-section pb-2">
          <div className="map-stats-ribbon" aria-label="Лимит ИИ">
            <div className="map-stats-ribbon-head">
              <p className="map-stats-ribbon-total m-0">
                <strong>{usage.remaining}</strong> из {usage.daily_limit} запросов сегодня
              </p>
              <p className="map-stats-ribbon-sync m-0">Лимит обновится завтра</p>
            </div>
          </div>
        </div>
      )}

      <nav className="classified-board-tabs mb-4" aria-label="Режим ИИ">
        <button
          type="button"
          className={`classified-board-tab${tab === "chat" ? " classified-board-tab--active" : ""}`}
          onClick={() => setTab("chat")}
        >
          <span className="classified-board-tab-icon" aria-hidden>💬</span>
          <span className="classified-board-tab-label">Чат</span>
        </button>
        <button
          type="button"
          className={`classified-board-tab${tab === "image" ? " classified-board-tab--active" : ""}`}
          onClick={() => setTab("image")}
        >
          <span className="classified-board-tab-icon" aria-hidden>🎨</span>
          <span className="classified-board-tab-label">Картинки</span>
        </button>
      </nav>

      {modelsLoading && <LiteraryInlineLoader label="Подключаем ИИ…" />}

      {modelsError && !modelsLoading && (
        <LiteraryEmptyState icon="⚠️" title="ИИ временно недоступен" text="Не удалось загрузить настройки. Попробуйте позже.">
          <button type="button" className="literary-btn literary-btn--primary mt-3" onClick={loadModels}>
            Повторить
          </button>
        </LiteraryEmptyState>
      )}

      {!modelsLoading && !modelsError && aiStatus && !aiStatus.ready && (
        <div className="ai-status-warn mb-4" role="status">
          <strong>ИИ временно недоступен</strong>
          <p className="m-0">{aiStatus.message}</p>
        </div>
      )}

      {!modelsLoading && !modelsError && limitReached && tab === "chat" && (
        <div className="ai-limits-note mb-4" role="status">
          <strong>Лимит на сегодня исчерпан</strong>
          <p className="m-0">Бесплатные сообщения обновятся завтра. Картинки — во вкладке «Картинки».</p>
          {usage?.payment_info?.message && <p className="mt-2 mb-0 text-sm">{usage.payment_info.message}</p>}
        </div>
      )}

      {!modelsLoading && !modelsError && tab === "chat" && (
        <div className="ai-literary-panel flex flex-col page-panel page-panel--forest p-0 overflow-hidden">
          {chatModels.length > 1 && (
            <div className="p-4 border-b border-border/60">
              <select className="pushkin-select w-full" value={chatModel} onChange={(e) => setChatModel(e.target.value)} aria-label="Режим чата">
                {chatModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[280px] max-h-[50vh]">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] whitespace-pre-wrap text-sm ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && <div className="chat-bubble-ai text-sm text-muted-foreground animate-pulse">Думаю…</div>}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-border/60 p-4">
            <div className="suggest-chips mb-2">
              {CHAT_SUGGESTIONS.map((s) => (
                <button key={s} type="button" className="suggest-chip" disabled={loading || limitReached} onClick={() => setInput(s)}>
                  {s}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-lg border bg-background px-4 py-3 text-sm pushkin-select"
                placeholder="Спросите что угодно…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                maxLength={1000}
                disabled={loading || limitReached}
              />
              <Button onClick={send} disabled={loading || limitReached || !input.trim()}>→</Button>
            </div>
          </div>
        </div>
      )}

      {!modelsLoading && !modelsError && tab === "image" && (
        <div className="page-panel page-panel--gold space-y-4">
          {imageModels.length > 1 && (
            <select className="pushkin-select w-full" value={imageModel} onChange={(e) => setImageModel(e.target.value)} aria-label="Стиль картинки">
              {imageModels.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          )}
          <div className="suggest-chips">
            {IMAGE_SUGGESTIONS.map((s) => (
              <button key={s} type="button" className="suggest-chip" onClick={() => setImagePrompt(s)}>
                {s}
              </button>
            ))}
          </div>
          <textarea
            className="literary-textarea w-full min-h-[80px]"
            placeholder="Опишите картинку на русском…"
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            maxLength={500}
          />
          <button
            type="button"
            className="literary-btn literary-btn--primary w-full"
            onClick={generateImage}
            disabled={imageLoading || !imagePrompt.trim()}
          >
            {imageLoading ? "Рисую…" : "🎨 Сгенерировать"}
          </button>
          {imageLoading && (
            <div className="ai-image-skeleton">
              <div className="ai-image-skeleton-shimmer" />
              <span>Генерация… до 60 сек</span>
            </div>
          )}
          {imageError && <p className="text-sm text-red-600 m-0">{imageError}</p>}
          {generatedImage && (
            <div className="space-y-2 ai-image-result">
              {imageProvider === "local-poster" && (
                <p className="text-xs text-amber-700 m-0">Не удалось нарисовать — попробуйте ещё раз</p>
              )}
              <img src={generatedImage} alt="Сгенерированная картинка" className="w-full rounded-lg border shadow-md" />
              <a href={generatedImage.split("?")[0]} download="pushkin-ai.jpg" className="literary-btn literary-btn--ghost text-sm inline-block no-underline">
                Скачать
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
