import { Link } from "react-router-dom";
import Brand from "../components/Brand";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Unavailable() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="flex items-center px-6 py-4">
        <Link to="/" aria-label="Mihur home">
          <Brand size="md" />
        </Link>
      </header>
      <div className="flex flex-1 items-center justify-center px-4 pb-16">
        <Card className="w-full max-w-md shadow-raised text-center">
          <CardHeader>
            <CardTitle className="text-xl">Not available in your region yet</CardTitle>
            <CardDescription>
              Mihur's private pilot currently serves families in the United
              States and Canada.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              If your family already has an approved account, sign in again to
              continue learning while you travel.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
