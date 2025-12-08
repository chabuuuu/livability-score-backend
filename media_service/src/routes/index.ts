import mediaRouter from "@/routes/media.route";

export function route(app: any) {
  app.use("/api/v1/media", mediaRouter);

  //Check health
  app.get(`/health`, (req: any, res: any) => {
    res.json({
      message: "OK",
    });
  });

  // Handle API not exists
  app.all("*", (req: any, res: any, next: any) => {
    res.status(404).json({
      message: "API not exists",
    });
  });
}
