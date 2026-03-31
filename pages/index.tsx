import KairosFrontend from '../frontend/KairosApp';
import Head from 'next/head';

export default function Home() {
  return (
    <>
      <Head>
        <title>Kairos - The Emergent Reasoning Network</title>
        <meta name="description" content="AI-powered reasoning and knowledge synthesis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
        <div className="container mx-auto px-4 py-8">
          <KairosFrontend />
        </div>
      </main>

      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="container mx-auto px-4 text-center">
          <p>© 2026 Kairos. Built by FranklinDAO.</p>
        </div>
      </footer>
    </>
  );
}