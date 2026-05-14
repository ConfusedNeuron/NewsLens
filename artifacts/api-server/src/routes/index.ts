import { Router, type IRouter } from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import healthRouter from "./health";

const router: IRouter = Router();

router.use(healthRouter);

router.use(
  "/",
  createProxyMiddleware({
    target: "http://localhost:8000",
    changeOrigin: true,
    pathRewrite: (path) => `/api${path}`,
    on: {
      error: (_err: Error, _req: any, res: any) => {
        res.status(502).json({ error: "Backend unavailable" });
      },
    },
  }),
);

export default router;
