import BaseError from "@/utils/base.error";
import { NextFunction, Request, Response } from "express";
import { ReasonPhrases, StatusCodes } from "http-status-codes";

/**
 * Middleware to handle the error before sending it to the client
 * @param error
 * @param req
 * @param res
 * @param next
 */
export const globalErrorHanlder = (
  error: any,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  console.error(error);

  if (error instanceof BaseError) {
    switch (error.code) {
      default:
        return res.send_internalServerError(error.message, error);
    }
  }

  return res.send_internalServerError(
    ReasonPhrases.INTERNAL_SERVER_ERROR,
    error.message
  );
};
