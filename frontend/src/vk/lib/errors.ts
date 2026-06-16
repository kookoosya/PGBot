/** Human-readable API and VK Bridge errors for Mini App UI. */

export function parseApiError(err: unknown): string {
  if (err instanceof TypeError && /fetch|network/i.test(err.message)) {
    return "Нет связи с сервером. Проверьте интернет и попробуйте снова.";
  }
  if (err instanceof Error) {
    const msg = err.message.trim();
    if (/401|unauthorized|не авторизован/i.test(msg)) {
      return "Сессия истекла. Мы попробуем войти через VK снова.";
    }
    if (/403|forbidden/i.test(msg)) {
      return "Недостаточно прав для этого действия.";
    }
    if (/422|validation/i.test(msg)) {
      return msg.length > 120 ? "Проверьте поля формы и попробуйте ещё раз." : msg;
    }
    if (/500|internal|server/i.test(msg)) {
      return "Сервер временно недоступен. Попробуйте чуть позже.";
    }
    if (msg && !msg.startsWith("HTTP ")) return msg;
  }
  return "Что-то пошло не так. Попробуйте ещё раз.";
}

export function vkAuthErrorMessage(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message;
    if (msg.includes("VITE_VK_APP_ID")) {
      return "Приложение ещё не настроено. Укажите ID мини-приложения в конфигурации.";
    }
    if (msg.includes("Откройте мини-приложение")) {
      return "Откройте портал из меню сообщества ВКонтакте.";
    }
    if (msg.includes("silent token") || msg.includes("VK не вернул")) {
      return "Не удалось получить доступ VK. Войдите в аккаунт и откройте приложение снова.";
    }
    if (/401|invalid|token/i.test(msg)) {
      return "VK не подтвердил вход. Закройте и откройте мини-приложение заново.";
    }
    return msg;
  }
  return "Не удалось войти через VK.";
}
