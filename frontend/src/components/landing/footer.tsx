import Link from "next/link";
import { Linkedin, Twitter } from "lucide-react";

const Footer = () => {
  const productLinks = [
    { label: "Features", href: "#features" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Examples", href: "#examples" },
  ];

  const companyLinks = [
    { label: "About", href: "#about" },
    { label: "Contact", href: "#contact" },
    { label: "Press", href: "#press" },
  ];

  const resourceLinks = [
    { label: "Help Center", href: "#help" },
    { label: "Guides", href: "#guides" },
    { label: "Updates", href: "#updates" },
  ];

  return (
    <footer className="border-accent bg-background w-full border-t py-12">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3 lg:grid-cols-4">
          {/* Left: Logo and Tagline */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-xl font-bold">
                Educational Video Generator
              </span>
            </Link>
            <p className="text-muted-foreground mt-4 text-sm">
              Your simple space to create educational videos, stay organized,
              and never lose a lesson idea.
            </p>
          </div>

          {/* Middle: Links */}
          <div className="grid grid-cols-3 gap-8 lg:col-span-2">
            <div>
              <h3 className="mb-4 text-sm font-semibold">Product</h3>
              <ul className="space-y-2">
                {productLinks.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold">Company</h3>
              <ul className="space-y-2">
                {companyLinks.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold">Resources</h3>
              <ul className="space-y-2">
                {resourceLinks.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right: Social Media */}
          <div className="lg:col-span-1">
            <h3 className="mb-4 text-sm font-semibold">Connect</h3>
            <div className="flex gap-4">
              <Link
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground flex h-10 w-10 items-center justify-center rounded-full border transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="h-5 w-5" />
              </Link>
              <Link
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground flex h-10 w-10 items-center justify-center rounded-full border transition-colors"
                aria-label="Twitter"
              >
                <Twitter className="h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 border-t pt-8">
          <p className="text-muted-foreground text-center text-sm">
            © 2025 Educational Video Generator. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
