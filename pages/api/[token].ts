import { NextApiRequest, NextApiResponse } from 'next';
import bot from "../../bot";

export default async (req: NextApiRequest, res: NextApiResponse) => {
  const {
    query: { token },
  } = req
  if (token !== process.env.BOT_TOKEN || req.method !== 'POST') {
    res.statusCode = 200;
    res.setHeader("X-TOKEN", token);
    res.end("");
    return;
  }
  await bot.handleUpdate(req.body, res);
  if (!res.writableEnded) {
    res.statusCode = 200;
    res.end();
  }
}
