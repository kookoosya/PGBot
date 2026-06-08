import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { api, AIModelOption, ChatMessage, PaymentInfo, UsageInfo } from "@/lib/api";

type Tab = "chat" | "image";

export function AIChat() {
  const [tab, setTab] = useState<Tab>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "🪶 Привет! Я универсальный ИИ-помощник Пушкинских Гор.\n\n" +
        "Могу ответить на любой вопрос, написать текст, подсказать идею.\n" +
        "Во вкладке «Картинки» — генерация изображений (Flux, Turbo…).",
    },
  ]);
  const [input, setInput] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [payment, setPayment] = useState<PaymentInfo | null>(null);
  const [chatModels, setChatModels] = useState<AIModelOption[]>([]);
  const [imageModels, setImageModels] = useState<AIModelOption[]>([]);
  const [capabilities, setCapabilities] = useState<string[]>([]);
  const [chatModel, setChatModel] = useState("pollinations");
  const [imageModel, setImageModel] = useState("flux");
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [imageProvider, setImageProvider] = useState<string | null>(null);
  const [imageError, setImageError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getAIUsage().then(setUsage).catch(console.error);
    api.getPaymentInfo().then(setPayment).catch(console.error);
    api.getAIModels().then((m) => {
      setChatModels(m.chat_models);
      setImageModels(m.image_models);
      setCapabilities(m.capabilities);
      if (m.chat_models[0]) setChatModel(m.chat_models[0].id);
      if (m.image_models[0]) setImageModel(m.image_models[0].id);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
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
    "Идеи для дачи на лето",
  ];

  const imageSuggestions = [
    "Усадьба в русском стиле, закат",
    "Памятник Пушкину в парке",
    "Уютная изба в снегу",
  ];

  return (
    <div className="page-section max-w-3xl">
      <PageHeader icon="🤖" title="ИИ-помощник" subtitle="Текст · картинки · любые задачи">
        {usage && (
          <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold bg-amber-400/20 border border-amber-400/40 text-amber-100">
            Сегодня: {usage.used} / {usage.daily_limit}
          </span>
        )}
      </PageHeader>

      {capabilities.length > 0 && (
        <div className="human-note mb-4 text-sm">
          <p className="font-semibold m-0 mb-2">ИИ умеет:</p>
          <ul className="m-0 pl-4 space-y-1">
            {capabilities.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <button
          type="button"
          className={`filter-chip ${tab === "chat" ? "filter-chip-active" : ""}`}
          onClick={() => setTab("chat")}
        >
          💬 Чат
        </button>
        <button
          type="button"
          className={`filter-chip ${tab === "image" ? "filter-chip-active" : ""}`}
          onClick={() => setTab("image")}
        >
          🎨 Картинки
        </button>
      </div>

      {tab === "chat" && (
        <>
          <div className="mb-3">
            <label className="text-xs text-muted-foreground">Модель чата</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm mt-1"
              value={chatModel}
              onChange={(e) => setChatModel(e.target.value)}
            >
              {chatModels.map((m) => (
                <option key={m.id} value={m.id}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="pushkin-card flex flex-col" style={{ height: "calc(100vh - 420px)", minHeight: 360 }}>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] whitespace-pre-wrap text-sm ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="chat-bubble-ai text-sm text-muted-foreground animate-pulse">🪶 Думаю…</div>
              )}
              <div ref={bottomRef} />
            </div>
            <div className="border-t p-4">
              <div className="suggest-chips">
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
                  disabled={loading}
                />
                <Button onClick={send} disabled={loading || !input.trim()}>→</Button>
              </div>
            </div>
          </div>
        </>
      )}

      {tab === "image" && (
        <div className="pushkin-card p-6 space-y-4">
          <div>
            <label className="text-xs text-muted-foreground">Модель картинки</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm mt-1"
              value={imageModel}
              onChange={(e) => setImageModel(e.target.value)}
            >
              {imageModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}{m.desc ? ` — ${m.desc}` : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="suggest-chips">
            {imageSuggestions.map((s) => (
              <button key={s} type="button" className="suggest-chip" onClick={() => setImagePrompt(s)}>
                {s}
              </button>
            ))}
          </div>
          <textarea
            className="w-full border rounded px-3 py-2 text-sm min-h-[80px]"
            placeholder="Опишите картинку на русском или английском…"
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            maxLength={500}
          />
          <Button className="w-full" onClick={generateImage} disabled={imageLoading || !imagePrompt.trim()}>
            {imageLoading ? "Рисую…" : "🎨 Сгенерировать"}
          </Button>
          {imageLoading && (
            <div className="w-full aspect-[4/3] rounded-lg border border-dashed border-primary/30 bg-primary/5 flex items-center justify-center text-sm text-muted-foreground animate-pulse">
              Генерация может занять до минуты…
            </div>
          )}
          {imageError && <p className="text-sm text-red-600">{imageError}</p>}
          {generatedImage && (
            <div className="space-y-2">
              {imageProvider && (
                <p className="text-xs text-muted-foreground m-0">
                  {imageProvider === "pollinations" && "✨ Сгенерировано Flux/Turbo (Pollinations)"}
                  {imageProvider === "google" && "✨ Сгенерировано Gemini Imagen"}
                  {imageProvider === "local-poster" &&
                    "🪶 Локальная иллюстрация — внешний генератор недоступен. Добавьте POLLINATIONS_API_KEY для реальных картинок."}
                  {imageProvider !== "pollinations" &&
                    imageProvider !== "google" &&
                    imageProvider !== "local-poster" &&
                    `Источник: ${imageProvider}`}
                </p>
              )}
              <img src={generatedImage} alt="Сгенерировано ИИ" className="w-full rounded-lg border shadow-md" />
              <a
                href={generatedImage.split("?")[0]}
                download="pushkin-ai.jpg"
                className="btn-hero-secondary text-sm inline-block no-underline"
              >
                Скачать
              </a>
            </div>
          )}
        </div>
      )}

      {payment && (
        <div className="mt-6 pushkin-card p-6 text-sm ai-payment-box">
          <h3 className="font-semibold mb-2">💳 Поддержать ИИ-помощник</h3>
          <p className="text-muted-foreground mb-2">
            Объявления, услуги и жалобы — <strong>бесплатно</strong>.
            ИИ после дневного лимита работает за счёт добровольных переводов.
          </p>
          <p className="text-muted-foreground mb-3">{payment.message}</p>
          <div className="payment-card-number">{payment.card_number}</div>
          <p className="text-xs text-muted-foreground mt-2">{payment.card_holder} · {payment.bank_name}</p>
        </div>
      )}
    </div>
  );
}
