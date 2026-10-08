import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "City Care Clinics — Multi-Agent AI Healthcare Assistant",
  description: "Next-generation clinical orchestration, patient memory, and human-in-the-loop doctor approval center.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body>{children}</body>
    </html>
  );
}
