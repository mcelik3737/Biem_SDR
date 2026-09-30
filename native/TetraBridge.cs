// Local adapter for the user's SDR# TETRA assembly. No SDR# UI or USB access.
using System;
using System.IO;
using System.Reflection;
using System.Collections;
using System.Collections.Generic;
using System.Web.Script.Serialization;

public unsafe class TetraBridge
{
    static BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    static Dictionary<string, int> Fields(object received, Type names)
    {
        var result = new Dictionary<string, int>();
        if (received == null) return result;
        var values = (int[])received.GetType().GetField("Data").GetValue(received);
        foreach (object key in Enum.GetValues(names)) {
            int index = Convert.ToInt32(key);
            if (index < values.Length && values[index] >= 0) result[key.ToString()] = values[index];
        }
        return result;
    }
    public static int Main(string[] args)
    {
        try {
            string directory = AppDomain.CurrentDomain.BaseDirectory;
            AppDomain.CurrentDomain.AssemblyResolve += (s,e) => Assembly.LoadFrom(Path.Combine(directory,new AssemblyName(e.Name).Name+".dll"));
            var assembly = Assembly.LoadFrom(Path.Combine(directory,"SDRSharp.Tetra.dll"));
            var demodType = assembly.GetType("SDRSharp.Tetra.Demodulator",true);
            var decoderType = assembly.GetType("SDRSharp.Tetra.TetraDecoder",true);
            var burstType = assembly.GetType("SDRSharp.Tetra.Burst",true);
            var names = assembly.GetType("SDRSharp.Tetra.GlobalNames",true);
            object demod = Activator.CreateInstance(demodType,true);
            object decoder = Activator.CreateInstance(decoderType,new object[]{null});
            object burst = Activator.CreateInstance(burstType);
            var process = demodType.GetMethod("ProcessBuffer",flags);
            var decode = decoderType.GetMethod("Process",flags);
            var input = Console.OpenStandardInput();
            var json = new JavaScriptSerializer();
            byte[] raw = new byte[510*8], bits = new byte[2048];
            float[] iq = new float[1020], symbols = new float[2048], audio = new float[480];
            Console.WriteLine("{\"ready\":true,\"input_rate\":96000}");
            while (true) {
                int read = 0;
                while (read < raw.Length) { int n=input.Read(raw,read,raw.Length-read); if(n==0)return 0; read+=n; }
                Buffer.BlockCopy(raw,0,iq,0,raw.Length);
                burstType.GetField("Mode").SetValue(burst,decoderType.GetProperty("TetraMode").GetValue(decoder,null));
                int slot;
                fixed(float* ip=iq, sp=symbols, ap=audio) fixed(byte* bp=bits) {
                    burstType.GetField("Ptr").SetValue(burst,Pointer.Box(bp,typeof(byte*)));
                    process.Invoke(demod,new object[]{burst,Pointer.Box(ip,process.GetParameters()[1].ParameterType),96000.0,510,Pointer.Box(sp,typeof(float*))});
                    if(burstType.GetField("Type").GetValue(burst).ToString()=="WaitBurst")continue;
                    slot=(int)decode.Invoke(decoder,new object[]{burst,Pointer.Box(ap,typeof(float*))});
                }
                bool received=(bool)decoderType.GetProperty("BurstReceived").GetValue(decoder,null);
                if(!received) continue;
                var data=new List<Dictionary<string,int>>();
                foreach(object entry in (IEnumerable)decoderType.GetField("_data",flags).GetValue(decoder)) data.Add(Fields(entry,names));
                var sync=Fields(decoderType.GetField("_syncInfo",flags).GetValue(decoder),names);
                // The original short PCM buffer avoids version-specific float gain.
                short[] pcm=(short[])decoderType.GetField("_sdc",flags).GetValue(decoder);
                byte[] bytes=new byte[pcm.Length*2]; Buffer.BlockCopy(pcm,0,bytes,0,bytes.Length);
                Console.WriteLine(json.Serialize(new {slot=slot, data=data, sync=sync,
                    errors=(bool)decoderType.GetProperty("HaveErrors").GetValue(decoder,null),
                    ber=decoderType.GetProperty("Ber").GetValue(decoder,null),
                    mode=decoderType.GetProperty("TetraMode").GetValue(decoder,null).ToString(),
                    pcm=slot>0 ? Convert.ToBase64String(bytes) : null}));
            }
        } catch(Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
