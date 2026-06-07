import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, ChatMessage, PaymentInfo, UsageInfo } from "@/lib/api";

export function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "🪶 Здравствуйте! Я ИИ-помощник Пушкинских Гор.\n\n" +
        "Спросите о поселке, быте, культуре — или помогу сформулировать обращение.\n" +
        "«Ученье — свет, а неученье — тьма» — так что спрашивайте смело!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [payment, setPayment] = useState<PaymentInfo | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getAIUsage().then(setUsage).catch(console.error);
    api.getPaymentInfo().then(setPayment).catch(console.error);
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

      const res = await api.sendAIChat(userMsg, history);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      setUsage({ used: res.daily_limit - res.remaining, remaining: res.remaining, daily_limit: res.daily_limit });
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Произошла ошибка. Попробуйте позже." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold">🤖 ИИ-помощник</h2>
        <p className="text-muted-foreground mt-2 font-serif italic">
          «Счастье то, что дух просветляет...»
        </p>
        {usage && (
          <p className="mt-3 text-sm">
            Сегодня: <strong>{usage.used}</strong> / {usage.daily_limit} сообщений
            {usage.remaining > 0 && (
              <span className="text-green-700"> · осталось {usage.remaining}</span>
            )}
          </p>
        )}
      </div>

      <div className="pushkin-card flex flex-col" style={{ height: "calc(100vh - 320px)", minHeight: 400 }}>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] whitespace-pre-wrap text-sm ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}`}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="chat-bubble-ai text-sm text-muted-foreground animate-pulse">
                🪶 Думаю...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t p-4">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-lg border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
              placeholder="Задайте вопрос..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              maxLength={1000}
              disabled={loading}
            />
            <Button onClick={send} disabled={loading || !input.trim()} className="px-6">
              →
            </Button>
          </div>
        </div>
      </div>

      {payment && (
        <div className="mt-6 pushkin-card p-6 text-sm">
          <h3 className="font-semibold text-base mb-2">💳 Поддержать ИИ-помощника</h3>
          <p className="text-muted-foreground mb-3">{payment.message}</p>
          <div className="grid gap-1 text-sm">
            <p>Карта: <strong className="font-mono">{payment.card_number}</strong></p>
            <p>Получатель: {payment.card_holder}</p>
            <p>Банк: {payment.bank_name}</p>
            <p>Сумма: от <strong>{payment.amount_suggested} ₽</strong></p>
            <p>Комментарий: «{payment.description}»</p>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            После перевода напишите на {payment.contact_email} — мы расширим лимит.
            Бесплатные сообщения обновляются каждый день.
          </p>
        </div>
      )}
    </div>
  );
}
