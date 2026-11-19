using System.Globalization;
using IPS.Engine.Game;
using IPS.Engine.Game.Buildings;
using IPS.Engine.Game.Jobs;
using UnityEngine;

namespace IPS.AndroidPort
{
    public static class NativeControls
    {
        private static AndroidJavaObject activity;
        private static float nextPoll;
        private static bool available;
        private static bool initializationFailed;

        public static void Tick(World world)
        {
            float now = Time.realtimeSinceStartup;
            if (initializationFailed || now < nextPoll)
                return;
            nextPoll = now + 0.1f;

            try
            {
                if (activity == null)
                {
                    using (var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
                        activity = player.GetStatic<AndroidJavaObject>("currentActivity");
                    if (activity == null)
                        return;
                }

                bool enabled = world != null && world.Brothel != null && Game.CurrentGameState == Game.GameState.Playing;
                if (available != enabled)
                {
                    available = enabled;
                    activity.Call("setCheatAvailability", enabled);
                }
                if (!enabled)
                    return;

                int action = activity.Call<int>("takeCheatAction");
                if (action == 0)
                    return;

                Brothel brothel = world.Brothel;
                switch (action)
                {
                    case 1:
                        ChangeGold(brothel, 100);
                        break;
                    case 2:
                        ChangeGold(brothel, -100);
                        break;
                    case 3:
                        ChangeReputation(brothel, 10f);
                        break;
                    case 4:
                        ChangeReputation(brothel, -10f);
                        break;
                }
            }
            catch (AndroidJavaException error)
            {
                initializationFailed = true;
                Debug.LogWarning("IPS Android controls: " + error.Message);
            }
        }

        private static void ChangeGold(Brothel brothel, int change)
        {
            int before = brothel.Gold;
            brothel.AddGold(change, GoldSource.None);
            Report(true, before.ToString(CultureInfo.InvariantCulture), brothel.Gold.ToString(CultureInfo.InvariantCulture));
        }

        private static void ChangeReputation(Brothel brothel, float change)
        {
            float before = brothel.Reputation;
            brothel.AddReputation(change);
            Report(false, before.ToString("0.##", CultureInfo.InvariantCulture), brothel.Reputation.ToString("0.##", CultureInfo.InvariantCulture));
        }

        private static void Report(bool gold, string before, string after)
        {
            Debug.Log("IPS Android debug " + (gold ? "gold: " : "reputation: ") + before + " -> " + after);
            activity.Call("reportCheatResult", gold, before, after);
        }
    }
}