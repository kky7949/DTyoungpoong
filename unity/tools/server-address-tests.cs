using System;
using Youngpoong.Integration;

public static class ServerAddressTests
{
    public static void Main()
    {
        Valid("  http://192.0.2.10:8001/  ", "http://192.0.2.10:8001");
        Valid("HTTPS://factory.example.com", "https://factory.example.com");
        Valid("http://[::1]:8001/", "http://[::1]:8001");
        Invalid(null, "blank handles null input");
        Invalid(" ", "blank can be handled by the local demo button");
        Invalid("192.0.2.10:8001", "requires an explicit scheme");
        Invalid("ftp://factory.example.com", "requires HTTP(S)");
        Invalid("http://user:pass@factory.example.com", "credentials are rejected");
        Invalid("http://@factory.example.com", "empty credentials are rejected");
        Invalid("http://factory.example.com/api/v1", "only the server origin is accepted");
        Invalid("http://factory.example.com/a/..", "a normalized path is still an entered path");
        Invalid("http://factory.example.com/?server=B", "queries are rejected");
        Invalid("http://factory.example.com/#B", "fragments are rejected");
        Invalid("http://factory.example.com:65536", "port must be valid");
        Invalid("http://factory.example.com:0", "port zero cannot identify the B listener");
        Invalid("http://factory.example.com\\path", "backslashes are rejected");
        Invalid("http://factory.example.com\t", "control characters are rejected");
        Console.WriteLine("PASS: 17 startup B server address cases.");
    }

    private static void Valid(string input, string expected)
    {
        string actual;
        if (!FactoryServerAddress.TryNormalize(input, out actual) || actual != expected)
            throw new Exception("Could not normalize " + input);
    }

    private static void Invalid(string input, string reason)
    {
        string actual;
        if (FactoryServerAddress.TryNormalize(input, out actual) || actual != "")
            throw new Exception("Unexpected address: " + input + " (" + reason + ")");
    }
}
