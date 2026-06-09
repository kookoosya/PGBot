import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function NotFound() {
  return (
    <div className="page-section max-w-lg mx-auto text-center py-16">
      <p className="text-5xl mb-4">🪶</p>
      <h1 className="text-2xl font-bold">Страница не найдена</h1>
      <p className="text-muted-foreground mt-3">
        Такого раздела на портале нет. Вернитесь на главную или выберите раздел в меню.
      </p>
      <div className="flex flex-wrap gap-3 justify-center mt-8">
        <Link to="/"><Button>На главную</Button></Link>
        <Link to="/map"><Button variant="outline">Карта</Button></Link>
        <Link to="/complaints"><Button variant="outline">Жалобы</Button></Link>
      </div>
    </div>
  );
}
