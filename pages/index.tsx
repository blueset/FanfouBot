import Head from 'next/head'
import styles from '../styles/Home.module.css'
import { InlineIcon } from "@iconify/react";
import telegram from "@iconify/icons-logos/telegram";

export default function Home() {
  return (
    <div className={styles.container}>
      <Head>
        <title>电磁炉</title>
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>电磁炉</h1>
        <p className={styles.description}>
          Telegram 用发饭 bot，单纯发饭｡
        </p>
        <div className={styles.grid}>
          <a href="https://t.me/buildalistbot" className={styles.card}>
            <p><InlineIcon icon={telegram} /> 开始使用</p>
          </a>

          <a href="https://github.com/blueset/fanfoubot" className={styles.card}>
            <p>查看源码</p>
          </a>
        </div>
      </main>
    </div>
  );
}
