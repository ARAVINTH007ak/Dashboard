import "../styles/globals.css";

export const metadata = {
  title: "Engineer Dashboard",
  description: "Engineer Impact Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}