import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import {
  api,
  AIAccessInfo,
  AIModelOption,
  AIPlan,
  AIStatus,
  ChatMessage,
  UsageInfo,
} from "@/lib/api";
import { useUserAuth } from "@/lib/userAuth";

type Tab = "chat" | "image" | "plans";

const CHAT_MODE_LABELS: Record<string, string> = {
  chat: "💬 Обычный чат",
  study: "📚 Учёба и тексты",
  code: "💻 Код",
};

export function AIChat() {
  const { user } = useUserAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useState<Tab>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "🪶 Привет! Без входа — 10 сообщений в день. После входа — пробный тариф (10/день, 7 дней). Дальше — платные тарифы во вкладке «Тарифы».",
    },
  ]);
  const [input, setInput] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [access, setAccess] = useState<AIAccessInfo | null>(null);
  const [plans, setPlans] = useState<AIPlan[]>([]);
  const [plansNotice, setPlansNotice] = useState("");
  const [chatModels, setChatModels] = useState<AIModelOption[]>([]);
  const [imageModels, setImageModels] = useState<AIModelOption[]>([]);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [chatModel, setChatModel] = useState("gemini-flash");
  const [chatMode, setChatMode] = useState("chat");
  const [imageModel, setImageModel] = useState("flux");
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [imageProvider, setImageProvider] = useState<string | null>(null);
  const [imageError, setImageError] = useState("");
  const [paymentInfo, setPaymentInfo] = useState<Awaited<ReturnType<typeof api.getPaymentInfo>> | null>(null);
  const [bankPayment, setBankPayment] = useState<Awaited<ReturnType<typeof api.createBankPaymentOrder>> | null>(null);
  const [payingPlanId, setPayingPlanId] = useState<string | null>(null);
  const [paymentNotice, setPaymentNotice] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshAccess = () => {
    api.getAIAccess().then(setAccess).catch(console.error);
    api.getAIUsage().then(setUsage).catch(console.error);
  };

  useEffect(() => {
    refreshAccess();
    api.getAIPlans().then((p) => {
      setPlans(p.plans);
      setPlansNotice(p.notice);
    }).catch(console.error);
    api.getPaymentInfo().then(setPaymentInfo).catch(console.error);
    api.getAIModels().then((m) => {
      setChatModels(m.chat_models);
      setImageModels(m.image_models);
      if (m.status) setAiStatus(m.status);
      const preferred = m.chat_models.find((x) => x.id === "gemini-flash")
        || m.chat_models.find((x) => x.id === "gemini")
        || m.chat_models.find((x) => x.fast)
        || m.chat_models[0];
      if (preferred) setChatModel(preferred.id);
      if (m.image_models[0]) setImageModel(m.image_models[0].id);
    }).catch(console.error);
  }, [user?.id]);

  useEffect(() => {
    if (access?.model_id) setChatModel(access.model_id);
    if (access?.chat_modes?.length && !access.chat_modes.includes(chatMode)) {
      setChatMode(access.chat_modes[0]);
    }
  }, [access, chatMode]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!user || tab !== "plans") return undefined;
    let cancelled = false;
    const poll = async () => {
      try {
        const latest = await api.getLatestAIPayment();
        if (cancelled) return;
        if (latest?.activated) {
          setPaymentNotice("Перевод получен — ИИ Pro активирован!");
          refreshAccess();
          return;
        }
        if (bankPayment || latest) {
          setPaymentNotice("Ожидаем перевод… Обычно 1–5 минут после оплаты с кодом в комментарии.");
        }
      } catch {
        /* ignore */
      }
    };
    void poll();
    const timer = window.setInterval(poll, 12000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [user?.id, tab, bankPayment?.order_id]);

  useEffect(() => {
    if (searchParams.get("paid") !== "1" || !user) return;

    setTab("plans");
    setPaymentNotice("Проверяем оплату…");
    let cancelled = false;

    const poll = async () => {
      for (let attempt = 0; attempt < 15 && !cancelled; attempt += 1) {
        try {
          const status = await api.getLatestAIPayment();
          if (status?.activated) {
            setPaymentNotice("Оплата прошла — доступ активирован автоматически.");
            refreshAccess();
            searchParams.delete("paid");
            setSearchParams(searchParams, { replace: true });
            return;
          }
        } catch {
          /* retry */
        }
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
      if (!cancelled) {
        setPaymentNotice(
          "Если деньги списались, доступ включится в течение минуты. Обновите страницу.",
        );
      }
    };

    void poll();
    return () => {
      cancelled = true;
    };
  }, [searchParams, setSearchParams, user?.id]);

  const payOnline = async (planId: string) => {
    setPayingPlanId(planId);
    setPaymentNotice("");
    try {
      const res = await api.subscribeAI(planId);
      window.location.href = res.payment_url;
    } catch (e) {
      setPaymentNotice(e instanceof Error ? e.message : "Не удалось создать платёж");
      setPayingPlanId(null);
    }
  };

  const requestBankPayment = async (planId: string) => {
    setPayingPlanId(planId);
    setPaymentNotice("");
    try {
      const res = await api.createBankPaymentOrder();
      setBankPayment(res);
      setPaymentNotice("Переведите точную сумму с кодом в комментарии — Pro включится сам.");
    } catch (e) {
      setPaymentNotice(e instanceof Error ? e.message : "Не удалось получить реквизиты");
    } finally {
      setPayingPlanId(null);
    }
  };

  const dailyLimit = access?.daily_limit ?? usage?.daily_limit ?? 10;
  const remaining = access?.remaining ?? usage?.remaining ?? dailyLimit;
  const limitReached = remaining <= 0;
  const isPaid = access?.is_paid ?? false;

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
      const res = await api.sendAIChat(userMsg, history, chatModel, chatMode);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      setUsage({ used: res.daily_limit - res.remaining, remaining: res.remaining, daily_limit: res.daily_limit });
      refreshAccess();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка. Попробуйте позже.";
      setMessages((m) => [...m, { role: "assistant", content: `⚠️ ${msg}` }]);
    } finally {
      setLoading(false);
    }
  };

  const generateImage = async () => {
    if (!imagePrompt.trim() || imageLoading || limitReached) return;
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
      refreshAccess();
    } catch (e) {
      setImageError(e instanceof Error ? e.message : "Ошибка генерации");
    } finally {
      setImageLoading(false);
    }
  };

  const suggestions = [
    "Напиши объявление про дрова",
    "Что посмотреть в Пушкиногорье?",
    "Проверь структуру реферата",
  ];

  const imageSuggestions = [
    "Усадьба в русском стиле, закат",
    "Памятник Пушкину в парке",
    "Уютная изба в снегу",
  ];

  return (
    <div className="page-section max-w-3xl ai-page">
      <PageHeader
        icon="🤖"
        title="ИИ-помощник"
        subtitle={access ? `Тариф: ${access.plan_name}` : "Текст и картинки"}
      >
        <span className="ai-usage-pill">
          {remaining} из {dailyLimit} сегодня
        </span>
      </PageHeader>

      {aiStatus && !aiStatus.ready && (
        <div className="ai-status-warn" role="status">
          <strong>ИИ временно недоступен</strong>
          <p>{aiStatus.message}</p>
        </div>
      )}

      <div className="ai-limits-info" role="note">
        <strong>Как это работает</strong>
        <p>
          Бесплатно — <strong>10 сообщений или картинок в день</strong> без входа. После{" "}
          {user ? (
            <>входа — тариф «{access?.plan_name ?? "…"}»</>
          ) : (
            <>
              <Link to="/cabinet/login">входа</Link> — пробный доступ 10 сообщений/день на 7 дней
            </>
          )}
          .
        </p>
        <p>
          Подписка <strong>ИИ Pro</strong> — перевод на карту или СБП с кодом в комментарии.
          Доступ включается <strong>автоматически</strong> — вам ничего подтверждать не нужно.
        </p>
        {access?.plan_id === "trial" && access.expires_at && (
          <p className="ai-limits-providers">
            Пробный период до {new Date(access.expires_at).toLocaleDateString("ru-RU")}
          </p>
        )}
        {isPaid && access?.plan_id !== "trial" && access?.expires_at && (
          <p className="ai-limits-providers">
            {access.plan_name} активен до {new Date(access.expires_at).toLocaleDateString("ru-RU")}
          </p>
        )}
      </div>

      {limitReached && (
        <div className="ai-limits-note" role="status">
          <strong>Лимит на сегодня исчерпан</strong>
          <p>
            {isPaid
              ? "Завтра счётчик обновится. Нужен больший объём — напишите администратору."
              : "Завтра снова будет 10 бесплатных сообщений. Пробный период и ИИ Pro — вкладка «Тарифы»."}
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-2 mb-4">
        <button type="button" className={`filter-chip ${tab === "chat" ? "filter-chip-active" : ""}`} onClick={() => setTab("chat")}>
          💬 Чат
        </button>
        <button type="button" className={`filter-chip ${tab === "image" ? "filter-chip-active" : ""}`} onClick={() => setTab("image")}>
          🎨 Картинки
        </button>
        <button type="button" className={`filter-chip ${tab === "plans" ? "filter-chip-active" : ""}`} onClick={() => setTab("plans")}>
          💳 Тарифы
        </button>
      </div>

      {tab === "plans" && (
        <div className="ai-plans-section space-y-4">
          {paymentNotice && (
            <p className="text-sm m-0 ai-limits-note" role="status">
              {paymentNotice}
            </p>
          )}
          <p className="text-sm text-muted-foreground m-0">{plansNotice}</p>
          <div className="ai-plans-grid">
            {plans.map((plan) => (
              <article
                key={plan.id}
                className={`ai-plan-card pushkin-card${access?.plan_id === plan.id ? " ai-plan-card--active" : ""}`}
              >
                <div className="ai-plan-head">
                  <h3>{plan.name}</h3>
                  {plan.price_rub > 0 ? (
                    <p className="ai-plan-price">{plan.price_rub} ₽ / {plan.period_days} дн.</p>
                  ) : (
                    <p className="ai-plan-price">0 ₽</p>
                  )}
                </div>
                <p className="ai-plan-tagline">{plan.tagline}</p>
                <ul className="ai-plan-features">
                  {plan.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
                {plan.requires_payment && (
                  <div className="ai-plan-pay">
                    {!user ? (
                      <p className="text-sm m-0">
                        <Link to="/cabinet/login">Войдите</Link>, чтобы оплатить и получить доступ.
                      </p>
                    ) : paymentInfo?.auto_payment_available ? (
                      <>
                        <Button
                          type="button"
                          className="w-full"
                          disabled={payingPlanId !== null}
                          onClick={() => payOnline(plan.id)}
                        >
                          {payingPlanId === plan.id
                            ? "Переход к оплате…"
                            : `Оплатить ${plan.price_rub} ₽ картой`}
                        </Button>
                        <p className="text-xs text-muted-foreground mt-2 m-0">
                          После оплаты доступ включится автоматически.
                        </p>
                      </>
                    ) : paymentInfo?.bank_transfer_available ? (
                      <>
                        <Button
                          type="button"
                          className="w-full"
                          disabled={payingPlanId !== null || isPaid}
                          onClick={() => requestBankPayment(plan.id)}
                        >
                          {payingPlanId === plan.id
                            ? "Готовим реквизиты…"
                            : `Получить реквизиты · ${plan.price_rub} ₽`}
                        </Button>
                        {bankPayment && (
                          <div className="text-sm space-y-2 mt-3">
                            <p className="m-0 font-semibold">Код: {bankPayment.payment_code}</p>
                            <p className="m-0">{bankPayment.instructions}</p>
                            {bankPayment.phone && (
                              <p className="m-0">📱 СБП: <span className="font-mono">{bankPayment.phone}</span></p>
                            )}
                            {bankPayment.card_number && (
                              <p className="m-0">💳 Карта: <span className="font-mono">{bankPayment.card_number}</span></p>
                            )}
                            <p className="m-0">{bankPayment.card_holder} · {bankPayment.bank_name}</p>
                          </div>
                        )}
                        <p className="text-xs text-muted-foreground mt-2 m-0">
                          После перевода с кодом Pro включится сам — обычно за 1–5 минут.
                        </p>
                      </>
                    ) : paymentInfo?.card_number ? (
                      <>
                        <p className="text-sm m-0 mb-2">
                          Перевод {plan.price_rub} ₽ с пометкой «ИИ {plan.name} · {user.username}»
                        </p>
                        <p className="text-sm m-0 font-mono">💳 {paymentInfo.card_number}</p>
                        <p className="text-sm m-0">{paymentInfo.card_holder}</p>
                        <p className="text-xs text-muted-foreground mt-2 m-0">
                          После перевода напишите администратору — доступ включится вручную.
                        </p>
                      </>
                    ) : (
                      <p className="text-sm m-0">Реквизиты уточняйте у администратора портала.</p>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        </div>
      )}

      {tab === "chat" && (
        <>
          {(access?.chat_modes?.length ?? 0) > 1 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {access?.chat_modes.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`filter-chip ${chatMode === mode ? "filter-chip-active" : ""}`}
                  onClick={() => setChatMode(mode)}
                >
                  {CHAT_MODE_LABELS[mode] || mode}
                </button>
              ))}
            </div>
          )}

          {chatModels.length > 1 && isPaid && (
            <div className="mb-3">
              <select className="w-full border rounded px-3 py-2 text-sm" value={chatModel} onChange={(e) => setChatModel(e.target.value)} aria-label="Модель">
                {chatModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
          )}

          <div className="pushkin-card ai-chat-panel flex flex-col">
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
        <div className="pushkin-card p-6 space-y-4">
          <p className="text-sm text-muted-foreground m-0">
            Картинки считаются в общий дневной лимит ({dailyLimit}/день).
          </p>
          {imageModels.length > 1 && (
            <select className="w-full border rounded px-3 py-2 text-sm" value={imageModel} onChange={(e) => setImageModel(e.target.value)} aria-label="Стиль картинки">
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
            disabled={limitReached}
          />
          <Button className="w-full" onClick={generateImage} disabled={imageLoading || limitReached || !imagePrompt.trim()}>
            {imageLoading ? "Рисую…" : "🎨 Сгенерировать"}
          </Button>
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
              <a href={generatedImage.split("?")[0]} download="pushkin-ai.jpg" className="btn-hero-secondary text-sm inline-block no-underline">
                Скачать
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
