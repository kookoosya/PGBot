import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { LITERARY_VERSES } from "@/lib/literaryCopy";
import { Button } from "@/components/ui/button";
import { api, AIModelOption, AIStatus, ChatMessage, UsageInfo } from "@/lib/api";

type Tab = "chat" | "image";

export function AIChat() {
  const [tab, setTab] = useState<Tab>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "🪶 Здравствуйте! Я помощник Пушкиногорья — подскажу про музеи, напишу объявление или стих. Спросите что угодно — или нарисуйте картинку во вкладке «Картинки».",
    },
  ]);
  const [input, setInput] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
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

  useEffect(() => {
    api.getAIUsage().then(setUsage).catch(console.error);
    api.getAIModels().then((m) => {
      setChatModels(m.chat_models);
      setImageModels(m.image_models);
      if (m.status) setAiStatus(m.status);
      const preferred = m.chat_models.find((x) => x.id === "gemini-flash") || m.chat_models[0];
      if (preferred) setChatModel(preferred.id);
      if (m.image_models[0]) setImageModel(m.image_models[0].id);
    }).catch(console.error);
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

  const suggestions = [
    "Напиши объявление про дрова",
    "Что посмотреть в Пушкиногорье?",
    "Напиши короткое стихотворение про зиму",
  ];

  const imageSuggestions = [
    "Усадьба в русском стиле, закат",
    "Памятник Пушкину в парке",
    "Уютная изба в снегу",
  ];

  return (
    <div className="page-section max-w-3xl ai-page">
      <PageHeader icon="🤖" title="ИИ-помощник" subtitle="Тексты, идеи и картинки — с душой Пушкиногорья">
        {usage && (
          <span className="ai-usage-pill">
            {usage.remaining} из {usage.daily_limit} сегодня
          </span>
        )}
      </PageHeader>

      {aiStatus && !aiStatus.ready && (
        <div className="ai-status-warn" role="status">
          <strong>ИИ временно недоступен</strong>
          <p>{aiStatus.message}</p>
        </div>
      )}

      {limitReached && (
        <div className="ai-limits-note" role="status">
          <strong>Лимит на сегодня исчерпан</strong>
          <p>Бесплатные сообщения обновятся завтра. Картинки — во вкладке «Картинки».</p>
          {usage?.payment_info && (
            <div className="mt-3 text-sm space-y-1">
              <p className="m-0">{usage.payment_info.message}</p>
              {usage.payment_info.card_number ? (
                <p className="m-0">
                  💳 {usage.payment_info.card_number}
                  {usage.payment_info.card_holder && ` · ${usage.payment_info.card_holder}`}
                  {" "}· от {usage.payment_info.amount_suggested} ₽
                </p>
              ) : null}
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <button type="button" className={`filter-chip ${tab === "chat" ? "filter-chip-active" : ""}`} onClick={() => setTab("chat")}>
          💬 Чат
        </button>
        <button type="button" className={`filter-chip ${tab === "image" ? "filter-chip-active" : ""}`} onClick={() => setTab("image")}>
          🎨 Картинки
        </button>
      </div>

      {tab === "chat" && (
        <>
          {chatModels.length > 1 && (
            <div className="mb-3">
              <select className="pushkin-select w-full" value={chatModel} onChange={(e) => setChatModel(e.target.value)} aria-label="Режим чата">
                {chatModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
          )}

          <div className="ai-literary-panel flex flex-col">
            <p className="ai-literary-welcome m-0">{LITERARY_VERSES.ai}</p>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
            <div className="border-t p-4">
              <div className="suggest-chips mb-2">
                {suggestions.map((s) => (
                  <button key={s} type="button" className="suggest-chip" disabled={loading} onClick={() => setInput(s)}>
                    {s}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  className="flex-1 rounded-lg border bg-background px-4 py-3 text-sm"
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
        </>
      )}

      {tab === "image" && (
        <div className="page-panel page-panel--gold p-6 space-y-4">
          {imageModels.length > 1 && (
            <select className="pushkin-select w-full" value={imageModel} onChange={(e) => setImageModel(e.target.value)} aria-label="Стиль картинки">
              {imageModels.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          )}
          <div className="suggest-chips">
            {imageSuggestions.map((s) => (
              <button key={s} type="button" className="suggest-chip" onClick={() => setImagePrompt(s)}>
                {s}
              </button>
            ))}
          </div>
          <textarea
            className="w-full border rounded px-3 py-2 text-sm min-h-[80px]"
            placeholder="Опишите картинку на русском…"
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            maxLength={500}
          />
          <button type="button" className="literary-btn literary-btn--primary w-full" onClick={generateImage} disabled={imageLoading || !imagePrompt.trim()}>
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
              <img src={generatedImage} alt="Картинка" className="w-full rounded-lg border shadow-md" />
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
