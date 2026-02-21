import "../styles/globals.css";

export const metadata = {
  title: "Engineer Impact Dashboard",
  description:
    "Top 5 impactful engineers based on last 5 days of repo activity",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="container">{children}</div>
      </body>
    </html>
  );
}
