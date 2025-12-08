import { MediaController } from "@/controllers/media.controller";
import uploadImageMiddleware from "@/middleware/upload-image.middleware";
import uploadVideoMiddleware from "@/middleware/upload-video.middleware";
import express from "express";

const mediaRouter = express.Router();

const mediaController = new MediaController();

mediaRouter
  .post(
    "/upload-video",
    uploadVideoMiddleware.single("file"),
    mediaController.uploadVideo.bind(mediaController)
  )

  .post(
    "/upload-image",
    uploadImageMiddleware.single("file"),
    mediaController.uploadImage.bind(mediaController)
  )

  .get("/video-url", mediaController.getVideoUrl.bind(mediaController));

export default mediaRouter;
