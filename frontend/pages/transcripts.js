import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import dynamic from 'next/dynamic';

// Dynamically import the TranscriptManager component
const DynamicTranscriptManager = dynamic(
  () => import('../components/TranscriptManager'),
  { ssr: false }
);

export default function Transcripts() {
  const [isClient, setIsClient] = useState(false);

  // Set isClient to true when component mounts
  useState(() => {
    setIsClient(true);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Interview Transcripts | AI Interview Agent</title>
        <meta name="description" content="Review and manage your interview transcripts" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white shadow">
        <div className="container mx-auto p-4 flex justify-between items-center">
          <Link href="/">
            <a className="flex items-center space-x-2">
              <svg
                className="h-8 w-8 text-blue-600"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
              <span className="text-xl font-semibold">AI Interview Agent</span>
            </a>
          </Link>
          <nav>
            <ul className="flex space-x-6">
              <li>
                <Link href="/">
                  <a className="text-gray-600 hover:text-blue-600 transition">Home</a>
                </Link>
              </li>
              <li>
                <Link href="/transcripts">
                  <a className="text-blue-600 font-medium">Transcripts</a>
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Interview Transcripts</h1>
          <p className="mt-2 text-gray-600">
            Review, search, and manage your interview session transcripts. Export transcripts for further analysis or import them from other sources.
          </p>
        </div>

        {isClient ? (
          <DynamicTranscriptManager />
        ) : (
          <div className="p-12 flex justify-center items-center">
            <div className="w-8 h-8 border-4 border-t-blue-600 border-r-transparent border-b-blue-600 border-l-transparent rounded-full animate-spin"></div>
            <p className="ml-3">Loading...</p>
          </div>
        )}
      </main>

      <footer className="bg-white border-t mt-12 py-8">
        <div className="container mx-auto px-4">
          <p className="text-center text-gray-500">
            &copy; {new Date().getFullYear()} AI Interview Agent | All rights reserved
          </p>
        </div>
      </footer>
    </div>
  );
} 