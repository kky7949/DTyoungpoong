using System;

namespace Youngpoong.Integration
{
    internal static class FactoryServerAddress
    {
        internal static bool TryNormalize(string input, out string address)
        {
            address = "";
            if (string.IsNullOrWhiteSpace(input)) return false;
            foreach (char character in input)
                if (char.IsControl(character)) return false;

            string value = input.Trim();
            int separator = value.IndexOf("://", StringComparison.Ordinal);
            if (separator < 0 || value.IndexOfAny(new[] { '\\', '?', '#', '@' }) >= 0)
                return false;

            int pathStart = value.IndexOf('/', separator + 3);
            if (pathStart >= 0 && pathStart != value.Length - 1) return false;

            Uri uri;
            if (!Uri.TryCreate(value, UriKind.Absolute, out uri) || !uri.IsWellFormedOriginalString() ||
                (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps) ||
                string.IsNullOrEmpty(uri.Host) || uri.Port == 0)
                return false;

            address = uri.GetLeftPart(UriPartial.Authority);
            return true;
        }
    }
}
